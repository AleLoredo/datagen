-- MS SQL Server Seed Data
-- Aligned with extras/seed_data.sql and postgres/seed.sql

CREATE DATABASE veterinaria_db;
GO

USE veterinaria_db;
GO

-- Create Database Connection User 'root_usr'
IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = N'root_usr')
BEGIN
    CREATE LOGIN [root_usr] WITH PASSWORD=N'Password123*', DEFAULT_DATABASE=[veterinaria_db], CHECK_EXPIRATION=OFF, CHECK_POLICY=OFF;
END
GO
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = N'root_usr')
BEGIN
    CREATE USER [root_usr] FOR LOGIN [root_usr];
    GRANT CONTROL TO [root_usr];
END
GO
EXEC sp_addrolemember 'db_owner', 'root_usr';
GO

-- 1. Roles
CREATE TABLE roles (
    id_rol INT IDENTITY(1,1) PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO roles (nombre_rol) VALUES 
('Veterinario'),
('Asistente'),
('Recepcionista'),
('Auxiliar'), 
('Cirujano'), 
('Peluquero'), 
('Anestesista'), 
('Laboratorista'), 
('Gerente'), 
('Limpieza');

-- 2. Especies
CREATE TABLE especies (
    id_especie INT IDENTITY(1,1) PRIMARY KEY,
    nombre_especie VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO especies (nombre_especie) VALUES 
('Perro'),
('Gato'),
('Ave'),
('Reptil'),
('Roedor'), 
('Equino'), 
('Bovino'), 
('Porcino'), 
('Caprino'), 
('Ovino');

-- 3. Usuarios
CREATE TABLE usuarios (
    id_usuario INT IDENTITY(1,1) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    id_rol INT NOT NULL,
    activo BIT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_rol) REFERENCES roles(id_rol)
);

INSERT INTO usuarios (username, password_hash, nombre, email, id_rol, activo) VALUES 
('user1', 'hash1', 'Juan Pérez', 'juan@vet.com', 1, 1),
('user2', 'hash2', 'Maria Lopez', 'maria@vet.com', 2, 1),
('user3', 'hash3', 'Carlos Ruiz', 'carlos@vet.com', 2, 1),
('user4', 'hash4', 'Ana Gomez', 'ana@vet.com', 3, 1),
('user5', 'hash5', 'Luis Torres', 'luis@vet.com', 4, 1),
('user6', 'hash6', 'Elena Diaz', 'elena@vet.com', 5, 1),
('user7', 'hash7', 'Pedro Silva', 'pedro@vet.com', 6, 1),
('user8', 'hash8', 'Sofia Castro', 'sofia@vet.com', 7, 1),
('user9', 'hash9', 'Miguel Angel', 'miguel@vet.com', 8, 1),
('user10', 'hash10', 'Laura Vega', 'laura@vet.com', 2, 1);

-- 4. Clientes
CREATE TABLE clientes (
    id_cliente INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    dni_cedula VARCHAR(20) NOT NULL UNIQUE,
    telefono VARCHAR(20),
    email VARCHAR(100),
    direccion TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO clientes (nombre, apellido, dni_cedula, telefono, email, direccion) VALUES 
('Roberto', 'Fernandez', '1001', '555-0101', 'roberto@mail.com', 'Calle 1'),
('Lucia', 'Martinez', '1002', '555-0102', 'lucia@mail.com', 'Calle 2'),
('Daniel', 'Sanchez', '1003', '555-0103', 'daniel@mail.com', 'Calle 3'),
('Camila', 'Ramirez', '1004', '555-0104', 'camila@mail.com', 'Calle 4'),
('Jorge', 'Hernandez', '1005', '555-0105', 'jorge@mail.com', 'Calle 5'),
('Valeria', 'Jimenez', '1006', '555-0106', 'valeria@mail.com', 'Calle 6'),
('Andres', 'Morales', '1007', '555-0107', 'andres@mail.com', 'Calle 7'),
('Paula', 'Ortiz', '1008', '555-0108', 'paula@mail.com', 'Calle 8'),
('Diego', 'Gutierrez', '1009', '555-0109', 'diego@mail.com', 'Calle 9'),
('Marta', 'Nuñez', '1010', '555-0110', 'marta@mail.com', 'Calle 10');

-- 5. Mascotas
CREATE TABLE mascotas (
    id_mascota INT IDENTITY(1,1) PRIMARY KEY,
    nombre_mascota VARCHAR(100) NOT NULL,
    id_especie INT NOT NULL,
    raza VARCHAR(50),
    fecha_nacimiento DATE,
    peso_kg DECIMAL(5,2),
    id_cliente INT NOT NULL,
    notas_medicas TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_especie) REFERENCES especies(id_especie),
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
);

INSERT INTO mascotas (nombre_mascota, id_especie, raza, fecha_nacimiento, peso_kg, id_cliente, notas_medicas) VALUES 
('Rex', 1, 'Pastor Aleman', '2020-01-01', 30.5, 1, 'Vacunas al dia'),
('Michi', 2, 'Siames', '2021-05-15', 4.2, 2, 'Esterilizado'),
('Tweety', 3, 'Canario', '2022-03-10', 0.1, 3, 'Control anual'),
('Dino', 4, 'Iguana', '2019-11-20', 2.0, 4, 'Revision escamas'),
('Jerry', 5, 'Hamster', '2023-01-01', 0.2, 5, 'Sano'),
('Spirit', 6, 'Mustang', '2015-06-01', 450.0, 6, 'Revision cascos'),
('Bessie', 7, 'Holstein', '2018-02-28', 600.0, 7, 'Produccion leche'),
('Porky', 8, 'Landrace', '2022-07-07', 150.0, 8, 'Engorde'),
('Billy', 9, 'Alpina', '2021-09-09', 45.0, 9, 'Control parásitos'),
('Dolly', 10, 'Merino', '2020-04-04', 50.0, 10, 'Esquila reciente');

-- 6. Citas
CREATE TABLE citas (
    id_cita INT IDENTITY(1,1) PRIMARY KEY,
    id_mascota INT NOT NULL,
    id_usuario INT NOT NULL,
    fecha_cita DATETIME NOT NULL,
    motivo TEXT,
    estado VARCHAR(20) DEFAULT 'Pendiente',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_mascota) REFERENCES mascotas(id_mascota),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

INSERT INTO citas (id_mascota, id_usuario, fecha_cita, motivo, estado) VALUES 
(1, 2, '2024-02-01 10:00:00', 'Vacunación', 'Pendiente'),
(2, 2, '2024-02-01 11:00:00', 'Consulta general', 'Completada'),
(3, 2, '2024-02-02 09:30:00', 'Corte de uñas', 'Pendiente'),
(4, 2, '2024-02-02 14:00:00', 'Revisión', 'Cancelada'),
(5, 2, '2024-02-03 16:00:00', 'Desparasitación', 'Pendiente'),
(6, 2, '2024-02-04 08:00:00', 'Emergencia', 'Completada'),
(7, 2, '2024-02-05 10:30:00', 'Cirugía', 'Pendiente'),
(8, 2, '2024-02-06 12:00:00', 'Control', 'Pendiente'),
(9, 2, '2024-02-07 15:00:00', 'Vacunación', 'Completada'),
(10, 2, '2024-02-08 09:00:00', 'Consulta dental', 'Pendiente');
GO
