/* =========================================================
   DATABASE
   ========================================================= */

CREATE DATABASE DriverMonitoringDB;
GO

USE DriverMonitoringDB;
GO


/* =========================================================
   1. ROLES
   ========================================================= */
CREATE TABLE ROLES (
    role_id INT IDENTITY(1,1) PRIMARY KEY,
    role_name VARCHAR(30) NOT NULL UNIQUE,
    description NVARCHAR(255),
    created_at DATETIME DEFAULT GETDATE()
);
GO


/* =========================================================
   2. USERS
   ========================================================= */
CREATE TABLE USERS (
    user_id VARCHAR(50) PRIMARY KEY,

    role_id INT NOT NULL,

    full_name NVARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    avatar_url VARCHAR(500),

    status VARCHAR(20) DEFAULT 'ACTIVE',

    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_USERS_ROLES
        FOREIGN KEY (role_id)
        REFERENCES ROLES(role_id)
);
GO


/* =========================================================
   3. VEHICLES
   ========================================================= */
CREATE TABLE VEHICLES (
    vehicle_id VARCHAR(50) PRIMARY KEY,

    user_id VARCHAR(50) NOT NULL,

    license_plate VARCHAR(20) NOT NULL UNIQUE,
    brand NVARCHAR(50),
    model NVARCHAR(50),
    manufacture_year INT,
    vehicle_type NVARCHAR(30),

    current_mileage FLOAT DEFAULT 0,

    inspection_expiry_date DATE,
    insurance_expiry_date DATE,

    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_VEHICLES_USERS
        FOREIGN KEY (user_id)
        REFERENCES USERS(user_id)
);
GO


/* =========================================================
   4. TRIPS
   ========================================================= */
CREATE TABLE TRIPS (
    trip_id VARCHAR(50) PRIMARY KEY,

    user_id VARCHAR(50) NOT NULL,
    vehicle_id VARCHAR(50) NOT NULL,

    start_time DATETIME NOT NULL,
    end_time DATETIME,

    start_latitude FLOAT,
    start_longitude FLOAT,

    end_latitude FLOAT,
    end_longitude FLOAT,

    distance_km FLOAT DEFAULT 0,
    duration_seconds INT DEFAULT 0,

    drowsiness_count INT DEFAULT 0,
    warning_count INT DEFAULT 0,

    status VARCHAR(20) DEFAULT 'ACTIVE',

    created_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_TRIPS_USERS
        FOREIGN KEY (user_id)
        REFERENCES USERS(user_id),

    CONSTRAINT FK_TRIPS_VEHICLES
        FOREIGN KEY (vehicle_id)
        REFERENCES VEHICLES(vehicle_id)
);
GO


/* =========================================================
   5. MONITORING_SESSIONS
   Không cần user_id vì lấy được từ TRIPS
   ========================================================= */
CREATE TABLE MONITORING_SESSIONS (
    session_id VARCHAR(50) PRIMARY KEY,

    trip_id VARCHAR(50) NOT NULL,

    start_time DATETIME NOT NULL,
    end_time DATETIME,

    total_frames INT DEFAULT 0,
    normal_frames INT DEFAULT 0,
    drowsy_frames INT DEFAULT 0,

    total_drowsiness_events INT DEFAULT 0,
    total_warning_events INT DEFAULT 0,

    average_perclos FLOAT DEFAULT 0,
    max_drowsy_duration FLOAT DEFAULT 0,

    status VARCHAR(20) DEFAULT 'ACTIVE',

    created_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_MONITORING_TRIPS
        FOREIGN KEY (trip_id)
        REFERENCES TRIPS(trip_id)
);
GO


/* =========================================================
   6. CAMERA_RECORDINGS
   ========================================================= */
CREATE TABLE CAMERA_RECORDINGS (
    recording_id VARCHAR(50) PRIMARY KEY,

    trip_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(50),

    recording_type VARCHAR(30),

    video_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),

    start_time DATETIME,
    end_time DATETIME,

    duration_seconds INT,
    file_size BIGINT,

    created_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_CAMERA_TRIPS
        FOREIGN KEY (trip_id)
        REFERENCES TRIPS(trip_id),

    CONSTRAINT FK_CAMERA_SESSIONS
        FOREIGN KEY (session_id)
        REFERENCES MONITORING_SESSIONS(session_id)
);
GO


/* =========================================================
   7. DROWSINESS_LOGS
   ========================================================= */
CREATE TABLE DROWSINESS_LOGS (
    log_id VARCHAR(50) PRIMARY KEY,

    trip_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(50) NOT NULL,
    recording_id VARCHAR(50),

    detected_at DATETIME NOT NULL,

    cnn_probability FLOAT,
    predicted_class VARCHAR(20),

    ear FLOAT,
    mar FLOAT,
    perclos FLOAT,

    cumulative_counter INT DEFAULT 0,

    eye_closed_duration FLOAT,
    drowsy_duration FLOAT,

    warning_level INT,
    warning_triggered BIT DEFAULT 0,

    latitude FLOAT,
    longitude FLOAT,

    created_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_DROWSINESS_TRIPS
        FOREIGN KEY (trip_id)
        REFERENCES TRIPS(trip_id),

    CONSTRAINT FK_DROWSINESS_SESSIONS
        FOREIGN KEY (session_id)
        REFERENCES MONITORING_SESSIONS(session_id),

    CONSTRAINT FK_DROWSINESS_RECORDINGS
        FOREIGN KEY (recording_id)
        REFERENCES CAMERA_RECORDINGS(recording_id)
);
GO


/* =========================================================
   8. MAINTENANCE_SCHEDULES
   Không cần user_id vì lấy từ VEHICLES
   ========================================================= */
CREATE TABLE MAINTENANCE_SCHEDULES (
    maintenance_id VARCHAR(50) PRIMARY KEY,

    vehicle_id VARCHAR(50) NOT NULL,

    maintenance_type VARCHAR(50),

    title NVARCHAR(100) NOT NULL,
    description NVARCHAR(MAX),

    scheduled_date DATETIME NOT NULL,
    reminder_date DATETIME,

    mileage_due FLOAT,

    notification_enabled BIT DEFAULT 1,

    status VARCHAR(20) DEFAULT 'PENDING',

    completed_at DATETIME,
    created_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_MAINTENANCE_VEHICLES
        FOREIGN KEY (vehicle_id)
        REFERENCES VEHICLES(vehicle_id)
);
GO


/* =========================================================
   9. REMINDERS
   vehicle_id có thể NULL vì có nhắc nhở không liên quan xe
   ========================================================= */
CREATE TABLE REMINDERS (
    reminder_id VARCHAR(50) PRIMARY KEY,

    user_id VARCHAR(50) NOT NULL,
    vehicle_id VARCHAR(50) NULL,

    title NVARCHAR(100) NOT NULL,
    description NVARCHAR(MAX),

    reminder_type VARCHAR(30),

    reminder_time DATETIME NOT NULL,

    repeat_type VARCHAR(20) DEFAULT 'NONE',

    enabled BIT DEFAULT 1,
    completed BIT DEFAULT 0,

    created_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_REMINDERS_USERS
        FOREIGN KEY (user_id)
        REFERENCES USERS(user_id),

    CONSTRAINT FK_REMINDERS_VEHICLES
        FOREIGN KEY (vehicle_id)
        REFERENCES VEHICLES(vehicle_id)
);
GO


/* =========================================================
   10. NOTIFICATIONS
   Notification type gộp trong cột type
   reference_id không đặt FK vì có thể tham chiếu nhiều bảng
   ========================================================= */
CREATE TABLE NOTIFICATIONS (
    notification_id VARCHAR(50) PRIMARY KEY,

    user_id VARCHAR(50) NOT NULL,

    type VARCHAR(30) NOT NULL,

    title NVARCHAR(100),
    message NVARCHAR(MAX),

    reference_id VARCHAR(50),

    is_read BIT DEFAULT 0,

    sent_at DATETIME,
    created_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_NOTIFICATIONS_USERS
        FOREIGN KEY (user_id)
        REFERENCES USERS(user_id)
);
GO


/* =========================================================
   11. USER_SETTINGS
   1 user chỉ có 1 settings
   ========================================================= */
CREATE TABLE USER_SETTINGS (
    setting_id VARCHAR(50) PRIMARY KEY,

    user_id VARCHAR(50) NOT NULL UNIQUE,

    drowsiness_alert_enabled BIT DEFAULT 1,
    alert_sound_enabled BIT DEFAULT 1,
    vibration_enabled BIT DEFAULT 1,

    maintenance_notification BIT DEFAULT 1,
    inspection_notification BIT DEFAULT 1,

    camera_recording_enabled BIT DEFAULT 1,
    save_drowsiness_video BIT DEFAULT 1,

    language VARCHAR(10) DEFAULT 'vi',
    theme VARCHAR(20) DEFAULT 'SYSTEM',

    updated_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_SETTINGS_USERS
        FOREIGN KEY (user_id)
        REFERENCES USERS(user_id)
);
GO


/* =========================================================
   12. MUSIC
   Nhạc và thể loại nhạc chung một bảng
   ========================================================= */
CREATE TABLE MUSIC (
    music_id VARCHAR(50) PRIMARY KEY,

    title NVARCHAR(150) NOT NULL,
    artist NVARCHAR(100),

    genre NVARCHAR(50),

    album NVARCHAR(100),

    duration INT,

    audio_url VARCHAR(500) NOT NULL,
    image_url VARCHAR(500),

    is_active BIT DEFAULT 1,

    created_at DATETIME DEFAULT GETDATE()
);
GO


/* =========================================================
   13. RADIO_STATIONS
   ========================================================= */
CREATE TABLE RADIO_STATIONS (
    radio_id VARCHAR(50) PRIMARY KEY,

    name NVARCHAR(100) NOT NULL,
    description NVARCHAR(MAX),

    category NVARCHAR(50),

    stream_url VARCHAR(500) NOT NULL,
    logo_url VARCHAR(500),

    is_active BIT DEFAULT 1,

    created_at DATETIME DEFAULT GETDATE()
);
GO


/* =========================================================
   14. TERMS
   ========================================================= */
CREATE TABLE TERMS (
    term_id VARCHAR(50) PRIMARY KEY,

    title NVARCHAR(150) NOT NULL,
    content NVARCHAR(MAX) NOT NULL,

    version VARCHAR(20) NOT NULL,

    term_type VARCHAR(30) NOT NULL,

    is_active BIT DEFAULT 1,

    effective_date DATETIME,

    created_at DATETIME DEFAULT GETDATE()
);
GO


/* =========================================================
   15. USER_TERM_ACCEPTANCE
   Bảng trung gian giữa USERS và TERMS
   ========================================================= */
CREATE TABLE USER_TERM_ACCEPTANCE (
    acceptance_id VARCHAR(50) PRIMARY KEY,

    user_id VARCHAR(50) NOT NULL,
    term_id VARCHAR(50) NOT NULL,

    accepted BIT DEFAULT 1,
    accepted_at DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_TERM_ACCEPTANCE_USERS
        FOREIGN KEY (user_id)
        REFERENCES USERS(user_id),

    CONSTRAINT FK_TERM_ACCEPTANCE_TERMS
        FOREIGN KEY (term_id)
        REFERENCES TERMS(term_id),

    CONSTRAINT UQ_USER_TERM
        UNIQUE (user_id, term_id)
);
GO