# AlistSync

基于[Alist](https://github.com/alist-org/alist/) API实现的简易的文件同步方案。

## ID类型

1. `backup_id`: 备份任务ID  
2. `copy_id`: 复制任务ID


## 初始化同步

策略一: `prefix`, 初始化时，向每一个重复文件前添加存储器前缀；  
策略二: `check_all`,让用户决定每一个需要保留的文件；  
策略三: `store:[STORE_NAME]` 让用户指定主同步存储器；  
 
## 同步进程

在前后两次的同步见 A 存储器 删除了文件 test.txt, 存储器 B 更新了文件 test.txt 应该如何处理？

## 旧文件保留策略

策略一：`not_save`, 不保留  
策略二: `single_dir`, 保留在同一目录下  
策略三: `backup_branch`,保留在Backup_id 目录下  

## 备份日志策略

new_table: `backup_log`  
key:  
    `time` 时间  
    `backup_id`  备份任务ID  
    `status`  记录状态  
    `copy_id`  复制ID


策略一: 