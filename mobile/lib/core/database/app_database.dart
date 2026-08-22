import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

/// Mở/khởi tạo SQLite DB cục bộ (tương đương RoomDatabase.getInstance()).
class AppDatabase {
  AppDatabase._();
  static final AppDatabase instance = AppDatabase._();

  static const _dbName = 'driver_safety.db';
  static const _dbVersion = 1;

  Database? _db;

  Future<Database> get database async => _db ??= await _open();

  Future<Database> _open() async {
    final dbPath = await getDatabasesPath();
    final path = p.join(dbPath, _dbName);
    return openDatabase(
      path,
      version: _dbVersion,
      onCreate: (db, version) => db.execute('''
        CREATE TABLE event_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          type TEXT NOT NULL,
          message TEXT NOT NULL,
          timestamp_ms INTEGER NOT NULL,
          confidence REAL,
          synced INTEGER NOT NULL DEFAULT 0
        )
      '''),
    );
  }
}
