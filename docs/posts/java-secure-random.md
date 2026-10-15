---
title: Java Secure Random
date: 2023-08-23T00:12:51+08:00
slug: java-secure-random
authors:
  - ihsin
categories:
  - Java
---

# Java Secure Random

Java标准库中的SecureRandom提供了一个密码学意义上的强随机数生成器。作为一个程序员，如果我们在JVM里出于安全考虑，想获取一个“真正随机”的数字，则很有可能将SecureRandom纳入考虑范围之内。
**然而使用它需要十分的小心。**

<!-- more -->

对SecureRandom起兴趣是因为一次对网络程序的排错，账号的登录过程十分缓慢。日志十分正常，没有任何警告或者错误。所以最初怀疑是某种逻辑错误导致的死循环。

jstack的thread dump如下

```
"main" #1 prio=5 os_prio=0 cpu=2745.71ms elapsed=56.22s tid=0x00007f2ec4014800 nid=0x2494 runnable  [0x00007f2ecde32000]
   java.lang.Thread.State: RUNNABLE
	at java.io.FileInputStream.readBytes(java.base@11.0.9.1/Native Method)
	at java.io.FileInputStream.read(java.base@11.0.9.1/FileInputStream.java:279)
	at java.io.FilterInputStream.read(java.base@11.0.9.1/FilterInputStream.java:133)
	at sun.security.provider.NativePRNG$RandomIO.readFully(java.base@11.0.9.1/NativePRNG.java:424)
	at sun.security.provider.NativePRNG$RandomIO.implGenerateSeed(java.base@11.0.9.1/NativePRNG.java:441)
	- locked <0x00000000ed00c680> (a java.lang.Object)
	at sun.security.provider.NativePRNG.engineGenerateSeed(java.base@11.0.9.1/NativePRNG.java:226)
	at java.security.SecureRandom.generateSeed(java.base@11.0.9.1/SecureRandom.java:857)
	at java.security.SecureRandom.getSeed(java.base@11.0.9.1/SecureRandom.java:840)
	at net.mamoe.mirai.internal.network.protocol.packet.login.wtlogin.WtLogin15Kt.get_mpasswd(WtLogin15.kt:136)
	at net.mamoe.mirai.internal.network.QQAndroidClient.<init>(QQAndroidClient.kt:268)
	at net.mamoe.mirai.internal.network.QQAndroidClient.<init>(QQAndroidClient.kt:72)
	at net.mamoe.mirai.internal.QQAndroidBot.initClient(QQAndroidBot.kt:62)
	at net.mamoe.mirai.internal.QQAndroidBot.<init>(QQAndroidBot.kt:59)
	at net.mamoe.mirai.internal.BotFactoryImpl.newBot(BotFactory.kt:34)
	at net.mamoe.mirai.BotFactory$INSTANCE.newBot(BotFactory.kt:115)
	at net.mamoe.mirai.console.MiraiConsole$INSTANCE.addBotImpl(MiraiConsole.kt:163)
	at net.mamoe.mirai.console.MiraiConsole$INSTANCE.addBot(MiraiConsole.kt:125)
	at net.mamoe.mirai.console.internal.MiraiConsoleImplementationBridge$doStart$11$1.invokeSuspend(MiraiConsoleImplementationBridge.kt:241)
	at kotlin.coroutines.jvm.internal.BaseContinuationImpl.resumeWith(ContinuationImpl.kt:33)
	at kotlinx.coroutines.DispatchedTask.run(DispatchedTask.kt:106)
	at kotlinx.coroutines.EventLoopImplBase.processNextEvent(EventLoop.common.kt:274)
	at kotlinx.coroutines.BlockingCoroutine.joinBlocking(Builders.kt:86)
	at kotlinx.coroutines.BuildersKt__BuildersKt.runBlocking(Builders.kt:61)
	at kotlinx.coroutines.BuildersKt.runBlocking(Unknown Source)
	at kotlinx.coroutines.BuildersKt__BuildersKt.runBlocking$default(Builders.kt)
	at kotlinx.coroutines.BuildersKt.runBlocking$default(Unknown Source)
	at net.mamoe.mirai.console.internal.MiraiConsoleImplementationBridge.doStart$mirai_console(MiraiConsoleImplementationBridge.kt:214)
	at net.mamoe.mirai.console.MiraiConsoleImplementation$Companion.start(MiraiConsoleImplementation.kt:209)
	at net.mamoe.mirai.console.terminal.MiraiConsoleTerminalLoader.startAsDaemon(MiraiConsoleTerminalLoader.kt:153)
	at net.mamoe.mirai.console.terminal.MiraiConsoleTerminalLoader.startAsDaemon$default(MiraiConsoleTerminalLoader.kt:152)
	at net.mamoe.mirai.console.terminal.MiraiConsoleTerminalLoader.main(MiraiConsoleTerminalLoader.kt:48)

   Locked ownable synchronizers:
	- <0x00000000ed5cf040> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)
```

可以看到程序阻塞在了`java.security.SecureRandom`和`java.io.FileInputStream.readBytes`。

看起来我们的 `SecureRandom` 在读取什么文件？如果你了解[类Unix系统](https://zh.wikipedia.org/wiki/%E7%B1%BBUnix%E7%B3%BB%E7%BB%9F)的话就不难猜出这个文件是 [`/dev/random`](https://zh.wikipedia.org/wiki//dev/random)。在GNU Linux上读取 `/dev/random` 这个设备文件就会得到随机的字节(试试 `cat /dev/random`?)。Linux系统会借助用户的鼠标输入、键盘输入、硬盘读取等环境噪声生成随机数。Linux将环境噪声保存在熵池中，使用`cat /proc/sys/kernel/random/entropy_avail`可以查看熵池的大小。显然在服务器环境下这些噪声较为稀少，这就导致了在服务器上 `/dev/random` 随机数生成缓慢。

