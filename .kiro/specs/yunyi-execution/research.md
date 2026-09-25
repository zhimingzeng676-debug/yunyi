# 调研与设计决策：执行与恢复

## 摘要
复杂集成：Windows进程管理、外部副作用与数据库事实之间没有单一事务。实验用隔离临时目录和自身创建的进程，不操作用户现有工程。

## 调研记录
- 父进程suspend后自身心跳停止，子进程仍增长；逐个暂停父子后均停止，恢复后继续。psutil不是原子进程树冻结。[psutil接口](https://psutil.readthedocs.io/en/latest/#psutil.Process.suspend)
- Windows暂停持锁线程可能阻塞协作，不能把暂停当作安全交接。[SuspendThread](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-suspendthread)
- pywin32 Job Object试验：挂起创建→加入Job→启动；查询包含父子PID；关闭设置KILL_ON_JOB_CLOSE的Job后父子均退出。见docs/evidence/windows-job.log。[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
- shell=False的参数含`&`和重定向文本时保留为字面值，没有生成注入目标文件。不能据此允许解释器-c或任意脚本。
- 实际文件字节快照能够保留原脏内容；after hash不匹配能够检测外部变更。该spike只验证原语，不证明产品回滚实现已完成。

## 决策
选择精确字节快照+受管动作；拒绝默认整仓checkout/stash。外部命令必须具名本地批准，并明确无通用沙箱保证。新文件、旧文件、补偿动作使用同一操作日志，未知结果不能自动重跑。

采用Windows Job Object控制生命周期、psutil查询身份，拒绝单纯kill父进程的方案。启动时附加失败关闭，避免失控子进程。

## 风险与待验
Job实验尚不替代交互TTY和真实Harness适配；产品仍需输出洪流、Ctrl+C、PID复用、junction/ADS/hardlink和崩溃阶段测试。恶意同用户并发写入不在普通文件快照的安全保证范围。

## 证据
docs/evidence/dependency-spikes.log、windows-job.log及.spikes/test_dependencies.py。原始试验代码留在.spikes，不复制为产品实现。
