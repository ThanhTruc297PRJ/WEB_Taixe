/// Loại sự kiện an toàn được phát hiện trên thiết bị.
enum EventType { drowsiness, distraction, systemInfo }

/// Một bản ghi log sự kiện lưu cục bộ (tương đương 1 row trong Room DB).
class EventLog {
  const EventLog({
    this.id,
    required this.type,
    required this.message,
    required this.timestamp,
    this.confidence,
    this.synced = false,
  });

  final int? id;
  final EventType type;
  final String message;
  final DateTime timestamp;
  final double? confidence;
  final bool synced;

  EventLog copyWith({int? id, bool? synced}) => EventLog(
        id: id ?? this.id,
        type: type,
        message: message,
        timestamp: timestamp,
        confidence: confidence,
        synced: synced ?? this.synced,
      );

  Map<String, Object?> toMap() => {
        if (id != null) 'id': id,
        'type': type.name,
        'message': message,
        'timestamp_ms': timestamp.millisecondsSinceEpoch,
        'confidence': confidence,
        'synced': synced ? 1 : 0,
      };

  factory EventLog.fromMap(Map<String, Object?> map) => EventLog(
        id: map['id'] as int?,
        type: EventType.values.byName(map['type'] as String),
        message: map['message'] as String,
        timestamp: DateTime.fromMillisecondsSinceEpoch(map['timestamp_ms'] as int),
        confidence: map['confidence'] as double?,
        synced: (map['synced'] as int) == 1,
      );
}
