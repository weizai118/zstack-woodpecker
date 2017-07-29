package org.zstack.header.storage.snapshot

import org.zstack.header.errorcode.ErrorCode

doc {

	title "快照回滚结果"

	ref {
		name "error"
		path "org.zstack.header.storage.snapshot.APIRevertVolumeFromSnapshotEvent.error"
		desc "错误码，若不为null，则表示操作失败, 操作成功时该字段为null",false
		type "ErrorCode"
		since "0.6"
		clz ErrorCode.class
	}
}