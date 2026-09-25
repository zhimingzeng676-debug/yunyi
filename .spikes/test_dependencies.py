"""Executable dependency experiments; not NetPilot implementation tests."""
import asyncio
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import psutil
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typer.testing import CliRunner
import typer
import win32api
import win32con
import win32job
import win32process

HERE = Path(__file__).parent
FLAGS = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

def wait_for(predicate, timeout=5):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError('condition did not become true')

def test_http_probe_distinguishes_auth_from_reachability():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(401)
            self.end_headers()
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with httpx.Client(timeout=0.2, trust_env=False) as client:
            response = client.get(f'http://127.0.0.1:{server.server_port}')
        assert response.status_code == 401
        assert response.is_success is False
    finally:
        server.shutdown()
        server.server_close()
        thread.join(2)

def test_windows_parent_pause_does_not_pause_child(tmp_path):
    proc = subprocess.Popen(
        [sys.executable, str(HERE / 'fake_worker.py'), str(tmp_path), 'parent'],
        creationflags=FLAGS,
    )
    owned = []
    try:
        wait_for(lambda: (tmp_path / 'child.pid').exists() and (tmp_path / 'child.ticks').exists())
        parent = psutil.Process(proc.pid)
        child = psutil.Process(int((tmp_path / 'child.pid').read_text()))
        owned = [parent, child]
        parent.suspend()
        p0 = (tmp_path / 'parent.ticks').stat().st_size
        c0 = (tmp_path / 'child.ticks').stat().st_size
        time.sleep(0.3)
        assert (tmp_path / 'parent.ticks').stat().st_size == p0
        assert (tmp_path / 'child.ticks').stat().st_size > c0
        child.suspend()
        c1 = (tmp_path / 'child.ticks').stat().st_size
        time.sleep(0.2)
        assert (tmp_path / 'child.ticks').stat().st_size == c1
        child.resume()
        parent.resume()
        wait_for(lambda: (tmp_path / 'parent.ticks').stat().st_size > p0)
        wait_for(lambda: (tmp_path / 'child.ticks').stat().st_size > c1)
    finally:
        for process in reversed(owned):
            try:
                process.resume()
                process.kill()
                process.wait(3)
            except psutil.NoSuchProcess:
                pass
        if proc.poll() is None:
            proc.kill()
        proc.wait(3)

def test_sqlite_single_claim_and_crash_rollback(tmp_path):
    db = tmp_path / 'spike.db'
    with sqlite3.connect(db) as conn:
        assert conn.execute('PRAGMA journal_mode=DELETE').fetchone()[0] == 'delete'
        conn.execute('PRAGMA synchronous=FULL')
        conn.execute('CREATE TABLE tasks(id TEXT PRIMARY KEY, status TEXT NOT NULL)')
        conn.execute("INSERT INTO tasks VALUES('one', 'pending')")
    claim = """
import sqlite3, sys
with sqlite3.connect(sys.argv[1],timeout=5) as c:
    c.execute('BEGIN IMMEDIATE')
    n=c.execute("UPDATE tasks SET status='running' WHERE id='one' AND status='pending'").rowcount
    print(n)
"""
    children = [subprocess.Popen([sys.executable, '-c', claim, str(db)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=FLAGS) for _ in range(2)]
    outputs = [p.communicate(timeout=10) for p in children]
    assert all(p.returncode == 0 for p in children)
    assert sorted(int(out[0]) for out in outputs) == [0, 1]
    crash = """
import sqlite3, sys, os
c=sqlite3.connect(sys.argv[1])
c.execute('BEGIN IMMEDIATE')
c.execute("UPDATE tasks SET status='succeeded' WHERE id='one'")
os._exit(23)
"""
    result = subprocess.run([sys.executable, '-c', crash, str(db)], creationflags=FLAGS, timeout=10)
    assert result.returncode == 23
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT status FROM tasks').fetchone()[0] == 'running'
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'

def test_windows_job_closes_owned_process_tree(tmp_path):
    job = win32job.CreateJobObject(None, '')
    limits = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
    limits['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, limits)
    command = subprocess.list2cmdline([sys.executable, str(HERE / 'fake_worker.py'), str(tmp_path), 'parent'])
    process_handle = thread_handle = None
    owned = []
    closed = False
    try:
        process_handle, thread_handle, pid, tid = win32process.CreateProcess(
            None, command, None, None, False,
            win32con.CREATE_SUSPENDED | win32con.CREATE_NO_WINDOW,
            None, None, win32process.STARTUPINFO(),
        )
        win32job.AssignProcessToJobObject(job, process_handle)
        win32process.ResumeThread(thread_handle)
        wait_for(lambda: (tmp_path / 'child.pid').exists() and (tmp_path / 'child.ticks').exists())
        child_pid = int((tmp_path / 'child.pid').read_text())
        owned = [psutil.Process(pid), psutil.Process(child_pid)]
        members = win32job.QueryInformationJobObject(job, win32job.JobObjectBasicProcessIdList)
        assert {pid, child_pid}.issubset(set(members))
        win32api.CloseHandle(job)
        closed = True
        for process in owned:
            process.wait(timeout=3)
        assert all(not process.is_running() for process in owned)
    finally:
        if not closed:
            win32api.CloseHandle(job)
        if thread_handle is not None:
            win32api.CloseHandle(thread_handle)
        if process_handle is not None:
            win32api.CloseHandle(process_handle)

def test_external_side_effect_survives_database_rollback(tmp_path):
    db = tmp_path / 'uncertain.db'
    effect = tmp_path / 'effect.txt'
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE steps(status TEXT)')
        conn.execute("INSERT INTO steps VALUES('running')")
    script = """
import os, sqlite3, sys
from pathlib import Path
c=sqlite3.connect(sys.argv[1])
c.execute('BEGIN IMMEDIATE')
Path(sys.argv[2]).write_text('side-effect-completed')
c.execute("UPDATE steps SET status='succeeded'")
os._exit(29)
"""
    result = subprocess.run([sys.executable, '-c', script, str(db), str(effect)], creationflags=FLAGS, timeout=10)
    assert result.returncode == 29
    assert effect.read_text() == 'side-effect-completed'
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT status FROM steps').fetchone()[0] == 'running'

def test_argv_shell_metacharacters_remain_literal(tmp_path):
    marker = tmp_path / 'must-not-exist.txt'
    argument = f'hello & echo polluted > "{marker}"'
    result = subprocess.run(
        [sys.executable, '-c', 'import sys; print(sys.argv[1])', argument],
        capture_output=True, text=True, shell=False, timeout=5, creationflags=FLAGS,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == argument
    assert not marker.exists()

def test_snapshot_preserves_dirty_bytes_and_detects_conflict(tmp_path):
    target = tmp_path / 'existing.txt'
    original = '用户原本的未提交内容\n'.encode('utf-8')
    target.write_bytes(original)
    snapshot = target.read_bytes()
    target.write_bytes(b'owned-change')
    expected_after = hashlib.sha256(target.read_bytes()).hexdigest()
    target.write_bytes(b'external-change')
    assert hashlib.sha256(target.read_bytes()).hexdigest() != expected_after
    assert target.read_bytes() == b'external-change'
    # A conflict-free restore can preserve the actual pre-task bytes, not HEAD.
    other = tmp_path / 'restored.txt'
    other.write_bytes(snapshot)
    assert other.read_bytes() == original

def test_mcp_stdio_handshake_schema_call_and_error():
    async def exercise():
        params = StdioServerParameters(
            command=sys.executable, args=[str(HERE / 'mcp_probe.py')],
            env={'PYTHONPATH': os.environ['PYTHONPATH'], 'PYTHONUTF8': '1'},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=10)) as session:
                info = await session.initialize()
                assert info.serverInfo.name == 'netpilot-dependency-spike'
                listed = await session.list_tools()
                assert [t.name for t in listed.tools] == ['echo_session']
                assert set(listed.tools[0].inputSchema['required']) == {'session_id', 'value'}
                result = await session.call_tool('echo_session', {'session_id': 'spike', 'value': 7})
                assert result.isError is False
                assert result.structuredContent == {'session_id': 'spike', 'value': 7}
                bad = await session.call_tool('echo_session', {'session_id': '', 'value': 7})
                assert bad.isError is True
    asyncio.run(exercise())

def test_cli_dependency_smoke():
    app = typer.Typer()
    @app.command()
    def status():
        typer.echo('spike-ready')
    runner = CliRunner()
    assert runner.invoke(app, ['--help']).exit_code == 0
    assert runner.invoke(app, []).stdout.strip() == 'spike-ready'
