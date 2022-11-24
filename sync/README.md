# 同步

## 数据结构


### FileRecode 结构
```yaml
store:
  sub_path:
    modified: time
    size: 1233
    hash: file_hash

store_2:
  sub_path_1:
    modified: time
    size: 222
    hash: file_hash
    
```

### SyncCache 结构
```yaml
store_1:  # 目标的Store
  sub_path:
    status: Init|MovingOld|CreateOldInfo|MovedOld|CopyingNew|CopiedNew|END
    source_store: 源文件所在存储器
    mate_data: |
      store_1/sub_path文件的元数据，方便后期写入移动后的JSON文件:
    ss: 
    
    
```
状态条件：  
`Init`: 创建复制任务的初始值；  
`MovingOld`: 创建Move任务成功后改变状态为此；  
`CreateOldInfo`: 检查Move完成，并创建metadata.json文件后改状态为此  
`MovedOld`：检查Move文件和metadata文件成功后改状态为此  
`CopyingNew`: 创建 Copy任务后改状态为此；  
`CopiedNew`: copy 任务完成后为此状态；  
`END`: 验证Copy文件完成，并更新 FileRecord 后变更记录为此；  
`DELETED`: 动作，下一次Sync扫描时，删除状态为END的项

## Sync逻辑

1. 扫描Alist文件信息；
2. 从FileRecord中提现原始记录信息