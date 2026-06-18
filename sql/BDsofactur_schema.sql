CREATE DATABASE BDsofactur;
GO

USE BDsofactur;
GO

CREATE TABLE Clientes (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    NombreClt VARCHAR(50) NOT NULL,
    ApellidoClt VARCHAR(50) NOT NULL,
    TelefonoClt INT NOT NULL,
    DireccionClt VARCHAR(100) NOT NULL,
    FechaRegistroClt DATETIME NOT NULL,
    CorreoClt VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Usuarios (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    ClienteId INT NULL,
    Nombre VARCHAR(50) NOT NULL,
    Email VARCHAR(100) NOT NULL,
    Contrasena VARCHAR(15) NOT NULL,
    Rol BIT NOT NULL,
    CONSTRAINT FK_Usuarios_Clientes FOREIGN KEY (ClienteId) REFERENCES Clientes(Id)
);

CREATE TABLE Contratos (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    ClienteId INT NOT NULL,
    Fecha_Inc DATE NOT NULL,
    Fecha_Fin DATE NOT NULL,
    EstadoContrato BIT NOT NULL,
    Descripcion VARCHAR(250) NOT NULL,
    CONSTRAINT CK_Contratos_Fechas CHECK (Fecha_Fin >= Fecha_Inc),
    CONSTRAINT FK_Contratos_Clientes FOREIGN KEY (ClienteId) REFERENCES Clientes(Id)
);

CREATE TABLE Servicios (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Nombre_Servicio VARCHAR(50) NOT NULL,
    Descripcion VARCHAR(200) NOT NULL,
    Precio INT NOT NULL,
    Duracion VARCHAR(50) NOT NULL
);

CREATE TABLE Facturas (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    UsuarioId INT NOT NULL,
    ContratoId INT NOT NULL,
    Fecha_Emision DATETIME NOT NULL,
    Fecha_Vencimiento DATETIME NOT NULL,
    Monto_Total DECIMAL(18,2) NOT NULL,
    CodigoFact INT NOT NULL UNIQUE,
    CONSTRAINT CK_Facturas_Fechas CHECK (Fecha_Vencimiento >= Fecha_Emision),
    CONSTRAINT FK_Facturas_Usuarios FOREIGN KEY (UsuarioId) REFERENCES Usuarios(Id),
    CONSTRAINT FK_Facturas_Contratos FOREIGN KEY (ContratoId) REFERENCES Contratos(Id)
);

CREATE TABLE Detalle_Factura (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    FacturaId INT NOT NULL,
    ServicioId INT NOT NULL,
    PrecioVenta INT NOT NULL,
    CONSTRAINT FK_DetalleFactura_Facturas FOREIGN KEY (FacturaId) REFERENCES Facturas(Id),
    CONSTRAINT FK_DetalleFactura_Servicios FOREIGN KEY (ServicioId) REFERENCES Servicios(Id)
);

CREATE TABLE Pagos (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Fecha_Pago DATETIME NOT NULL,
    Monto_Pagado DECIMAL(18,2) NOT NULL,
    EstadoPago BIT NOT NULL,
    MetodoPago BIT NOT NULL,
    FacturaId INT NOT NULL,
    NumeroRecibo INT NOT NULL UNIQUE,
    CONSTRAINT FK_Pagos_Facturas FOREIGN KEY (FacturaId) REFERENCES Facturas(Id)
);

CREATE TABLE Mora (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Fecha_Inicio DATETIME NOT NULL,
    Fecha_Final DATETIME NOT NULL,
    Monto_Mora DECIMAL(18,2) NOT NULL,
    PagoId INT NOT NULL,
    DescripcionMora VARCHAR(500) NOT NULL,
    CONSTRAINT CK_Mora_Fechas CHECK (Fecha_Final >= Fecha_Inicio),
    CONSTRAINT FK_Mora_Pagos FOREIGN KEY (PagoId) REFERENCES Pagos(Id)
);

CREATE TABLE Notificaciones (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    ClienteId INT NOT NULL,
    Fecha_Envio DATETIME NOT NULL,
    Mensaje VARCHAR(250) NOT NULL,
    EstadoNotificacion BIT NOT NULL,
    CONSTRAINT FK_Notificaciones_Clientes FOREIGN KEY (ClienteId) REFERENCES Clientes(Id)
);

CREATE TABLE LogAuditoria (
    IdLog INT IDENTITY(1,1) PRIMARY KEY,
    Tabla NVARCHAR(128) NOT NULL,
    Accion NVARCHAR(20) NOT NULL,
    ClavePrincipal NVARCHAR(128) NULL,
    Usuario NVARCHAR(128) NOT NULL CONSTRAINT DF_LogAuditoria_Usuario DEFAULT SYSTEM_USER,
    Host NVARCHAR(128) NOT NULL CONSTRAINT DF_LogAuditoria_Host DEFAULT HOST_NAME(),
    Fecha DATETIME2(3) NOT NULL CONSTRAINT DF_LogAuditoria_Fecha DEFAULT SYSDATETIME(),
    Detalle NVARCHAR(4000) NULL
);
