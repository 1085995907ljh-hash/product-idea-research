# Agent Reach 与权限

Apple辅助脚本优先使用Python HTTPS；若本机Python缺少信任证书，使用系统curl保留TLS验证。二者都失败时标记unavailable，不关闭证书验证。

必须依赖Agent Reach做研究路由，不复制其账号配置。要求只读公网、执行可信CLI、读输入文件、写本次目录；动态/登录内容需已有浏览器授权与站点登录。Skill不能自动给宿主提权。

1. 定位并阅读当前Agent Reach SKILL.md。没有则标not_configured、查官方安装，不远程管道执行。
2. `agent-reach doctor --json`；preflight.py保存状态；按active_backend读取对应search/social/web参考。开始时说明后端。
3. 真正读取所需资料才算本轮可用；doctor的ok不证明额度、登录和目标页可用。失败按文档有限重试，保留原因。
4. 美国消费者优先本地英语原始资料，不为多平台而搜无关中文内容。公开商店API适配器仅取美区元数据/评论，不买App、不登录、不估收入。

搜索摘要只定位，原文才证明。Trends用真CSV/点位，US默认近一月/三月/12月，记录比较组、类别、类型、粒度、部分周期；无法获取就不画。Apple Ads无账户标未核实，不用其他热度冒充。

缺扩展/登录/付费账号先做独立工作；只有缺口实质影响判断且公开来源无法补足才说明需要什么。不得申请笼统所有权限、索取明文Cookie、访问他人账号或购买数据。遵守宿主浏览器安全约束，不换协议绕过拒绝。

Agent Reach临时文件遵循其/tmp与用户目录规则，正式研究结果可写用户本次目录。分享包不含本机access.json、令牌、Cookie或账号配置。官方项目：https://github.com/Panniantong/Agent-Reach 。能力和命令以当前安装文档与实测为准。
