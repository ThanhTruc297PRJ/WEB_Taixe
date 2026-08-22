import '../../core/database/app_database.dart';
import '../models/event_log.dart';

/// DAO-equivalent: CRUD cho bảng event_log.
class EventLogRepository {
  EventLogRepository({AppDatabase? database}) : _database = database ?? AppDatabase.instance;

  final AppDatabase _database;

  Future<EventLog> insert(EventLog log) async {
    final db = await _database.database;
    final id = await db.insert('event_log', log.toMap());
    return log.copyWith(id: id);
  }

  Future<List<EventLog>> recent({int limit = 50}) async {
    final db = await _database.database;
    final rows = await db.query(
      'event_log',
      orderBy: 'timestamp_ms DESC',
      limit: limit,
    );
    return rows.map(EventLog.fromMap).toList();
  }

  Future<List<EventLog>> unsynced() async {
    final db = await _database.database;
    final rows = await db.query('event_log', where: 'synced = 0');
    return rows.map(EventLog.fromMap).toList();
  }

  Future<void> markSynced(int id) async {
    final db = await _database.database;
    await db.update(
      'event_log',
      {'synced': 1},
      where: 'id = ?',
      whereArgs: [id],
    );
  }
}
