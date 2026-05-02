# Scale Hardening Contracts

Required contracts:

- `QueueTopologySpec`
- `QueueItem`
- `ShardLease`
- `RetryDeadLetterRecord`
- `BackpressureSignal`
- `AutoscalingDecision`
- `ScaleRecoveryReport`
- `ScaleFixtureManifest`

Required commands:

- `record_queue_topology`
- `record_queue_item`
- `record_shard_lease`
- `record_backpressure_signal`
- `record_autoscaling_decision`
- `record_retry_dead_letter`
- `record_scale_recovery_report`

Required events:

- `queue_topology_recorded`
- `queue_item_recorded`
- `shard_lease_recorded`
- `backpressure_signal_recorded`
- `autoscaling_decided`
- `retry_dead_letter_recorded`
- `scale_recovery_reported`

Required fixtures:

- `scale-sharding-success`
- `backpressure-autoscale-success`
- `dead-letter-recovery-success`
- `stale-lease-without-recovery`
- `unfair-site-starvation`
- `autoscale-without-policy`
- `dead-letter-missing-failure-record`
- `replay-missing-scale-refs`
