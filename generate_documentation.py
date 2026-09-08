#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para generar documentación en Word del proyecto SoftFactur
Documenta clases, métodos y política de seguridad
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

def add_heading_style(doc, text, level=1):
    """Agrega un encabezado con estilo"""
    heading = doc.add_heading(text, level=level)
    return heading

def add_colored_paragraph(doc, text, color=None, bold=False, italic=False, size=11):
    """Agrega un párrafo con formato personalizado"""
    p = doc.add_paragraph(text)
    if color:
        for run in p.runs:
            run.font.color.rgb = color
    for run in p.runs:
        if bold:
            run.font.bold = True
        if italic:
            run.font.italic = True
        run.font.size = Pt(size)
    return p

def set_cell_background(cell, fill):
    """Establece el fondo de una celda de tabla"""
    shading_elm = OxmlElement('w:shd')
    shading_elm.set(qn('w:fill'), fill)
    cell._element.get_or_add_tcPr().append(shading_elm)

def create_softfactur_documentation():
    """Crea el documento de documentación de SoftFactur"""
    
    doc = Document()
    
    # ========== PORTADA ==========
    title = doc.add_heading('SOFTFACTUR', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    subtitle = doc.add_heading('Documentación Técnica del Sistema', level=2)
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    
    info = doc.add_paragraph('Clases Importantes, Métodos y Política de Seguridad')
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    info.runs[0].font.size = Pt(14)
    
    doc.add_paragraph()
    doc.add_paragraph()
    
    fecha = doc.add_paragraph(f'Fecha: {datetime.datetime.now().strftime("%d de %B de %Y")}')
    fecha.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_page_break()
    
    # ========== TABLA DE CONTENIDOS ==========
    doc.add_heading('Tabla de Contenidos', level=1)
    toc_items = [
        '1. Introducción al Proyecto',
        '2. Política de Seguridad con Django',
        '3. Cifrado de Contraseñas',
        '4. Clases Principales del Sistema',
        '5. Modelos de Datos Clave',
        '6. API y Autenticación',
        '7. Mecanismos Adicionales de Seguridad',
        '8. Buenas Prácticas Recomendadas'
    ]
    
    for item in toc_items:
        doc.add_paragraph(item, style='List Number')
    
    doc.add_page_break()
    
    # ========== 1. INTRODUCCIÓN ==========
    doc.add_heading('1. Introducción al Proyecto', level=1)
    doc.add_paragraph(
        'SoftFactur es un sistema de gestión de facturación y contratación desarrollado con Django 4.2, '
        'diseñado para manejar operaciones de negocio complejas incluyendo usuarios, clientes, contratos, '
        'facturas, pagos, auditoría y notificaciones. El proyecto implementa una arquitectura robusta '
        'con énfasis en seguridad, auditoría y separación de responsabilidades.'
    )
    
    doc.add_heading('Características Principales:', level=2)
    features = [
        'Gestión de usuarios con roles y permisos',
        'Módulo de seguridad con autenticación y recuperación de contraseña',
        'Catálogos de referencia (clientes, departamentos, servicios, etc.)',
        'Transacciones completas (facturas, contratos, pagos, mora)',
        'Sistema de auditoría para registrar cambios',
        'API RESTful con Django REST Framework',
        'Base de datos SQL Server con transacciones seguras'
    ]
    for feature in features:
        doc.add_paragraph(feature, style='List Bullet')
    
    doc.add_page_break()
    
    # ========== 2. POLÍTICA DE SEGURIDAD CON DJANGO ==========
    doc.add_heading('2. Política de Seguridad con Django', level=1)
    
    doc.add_heading('2.1 Configuración de Seguridad', level=2)
    doc.add_paragraph(
        'Django proporciona múltiples capas de seguridad que SoftFactur implementa:',
        style='List Bullet'
    )
    
    security_items = [
        ('Middleware de Seguridad', 'SecurityMiddleware: Protege contra ataques comunes como clickjacking (X-Frame-Options).'),
        ('CSRF Protection', 'CsrfViewMiddleware: Protege contra ataques Cross-Site Request Forgery (CSRF).'),
        ('Session Security', 'SessionMiddleware: Gestiona sesiones seguras de usuario con cookies seguras.'),
        ('Authentication Middleware', 'AuthenticationMiddleware: Verifica y autentica usuarios en cada solicitud.'),
        ('CORS Personalizado', 'DevCorsMiddleware: Controlador personalizado para compartir recursos entre orígenes.'),
    ]
    
    for title, desc in security_items:
        p = doc.add_paragraph()
        p.add_run(title + ': ').bold = True
        p.add_run(desc)
    
    doc.add_heading('2.2 Configuración de Base de Datos', level=2)
    doc.add_paragraph(
        'El sistema utiliza SQL Server con autenticación de Windows integrada:'
    )
    
    table = doc.add_table(rows=5, cols=2)
    table.style = 'Light Grid Accent 1'
    
    headers = table.rows[0].cells
    headers[0].text = 'Parámetro'
    headers[1].text = 'Valor'
    set_cell_background(headers[0], 'D3D3D3')
    set_cell_background(headers[1], 'D3D3D3')
    
    data = [
        ('Motor (ENGINE)', 'SoftFactur.db.backends.mssql_no_mars'),
        ('Nombre BD', 'BDsofactur'),
        ('Host', 'localhost:1433'),
        ('Autenticación', 'Trusted Connection (Windows Auth)')
    ]
    
    for i, (key, value) in enumerate(data, 1):
        row = table.rows[i].cells
        row[0].text = key
        row[1].text = value
    
    doc.add_heading('2.3 Validadores de Contraseña', level=2)
    doc.add_paragraph(
        'Django proporciona validadores incorporados que se utilizan en SoftFactur:'
    )
    
    validators = [
        ('UserAttributeSimilarityValidator', 'Verifica que la contraseña no sea similar al nombre de usuario o email.'),
        ('MinimumLengthValidator', 'Asegura que la contraseña tenga una longitud mínima (por defecto 8 caracteres).'),
        ('CommonPasswordValidator', 'Verifica contra una lista de contraseñas comunes (top 20,000 más usadas).'),
        ('NumericPasswordValidator', 'Rechaza contraseñas que sean completamente numéricas.')
    ]
    
    for validator, description in validators:
        p = doc.add_paragraph()
        p.add_run(validator + ': ').bold = True
        p.add_run(description)
    
    doc.add_page_break()
    
    # ========== 3. CIFRADO DE CONTRASEÑAS ==========
    doc.add_heading('3. Cifrado de Contraseñas', level=1)
    
    doc.add_heading('3.1 Librería Principal: PBKDF2', level=2)
    doc.add_paragraph(
        'Django utiliza PBKDF2 (Password-Based Key Derivation Function 2) como el algoritmo de hash por defecto. '
        'Este es un algoritmo seguro y ampliamente reconocido que es parte del estándar PKCS #5.'
    )
    
    doc.add_heading('Características de PBKDF2:', level=3)
    pbkdf2_features = [
        'Algoritmo iterativo: Realiza múltiples iteraciones (240,000 por defecto en Django)',
        'Salt: Utiliza un salt único por contraseña, generado aleatoriamente',
        'Función hash: Utiliza SHA256 (configurable)',
        'Resistencia a ataques: Diseñado para ser resistente a ataques de fuerza bruta'
    ]
    for feature in pbkdf2_features:
        doc.add_paragraph(feature, style='List Bullet')
    
    doc.add_heading('3.2 Formato de Almacenamiento', level=2)
    doc.add_paragraph(
        'Las contraseñas en Django se almacenan en el siguiente formato:'
    )
    
    code_para = doc.add_paragraph()
    code_para.add_run('pbkdf2_sha256$240000$salt$hash').font.name = 'Courier New'
    code_para.add_run(' ').font.size = Pt(10)
    
    doc.add_paragraph()
    
    storage_table = doc.add_table(rows=5, cols=2)
    storage_table.style = 'Light Grid Accent 1'
    
    headers = storage_table.rows[0].cells
    headers[0].text = 'Componente'
    headers[1].text = 'Descripción'
    set_cell_background(headers[0], 'D3D3D3')
    set_cell_background(headers[1], 'D3D3D3')
    
    storage_data = [
        ('pbkdf2_sha256', 'Identificador del algoritmo y función hash'),
        ('240000', 'Número de iteraciones para derivar la clave'),
        ('salt', 'Valor aleatorio único para cada contraseña'),
        ('hash', 'Hash resultante de la función PBKDF2')
    ]
    
    for i, (component, description) in enumerate(storage_data, 1):
        row = storage_table.rows[i].cells
        row[0].text = component
        row[1].text = description
    
    doc.add_heading('3.3 Métodos de Cifrado en SoftFactur', level=2)
    
    code_example = doc.add_paragraph()
    code_example.add_run('# Ejemplo en el serializer:').font.name = 'Courier New'
    code_example.runs[0].font.size = Pt(9)
    
    code_lines = [
        'user.set_password(nueva_contrasena)  # Usa PBKDF2',
        'user.save()  # Almacena el hash en la BD',
    ]
    
    for line in code_lines:
        p = doc.add_paragraph()
        p.add_run(line).font.name = 'Courier New'
        p.runs[0].font.size = Pt(9)
    
    doc.add_page_break()
    
    # ========== 3.4 OTROS TIPOS DE CIFRADO ==========
    doc.add_heading('3.4 Otros Tipos de Cifrado y Sus Usos', level=2)
    
    encryption_types = [
        {
            'nombre': 'Base64',
            'uso': 'Codificación de UID en enlaces de recuperación de contraseña',
            'seguridad': 'Baja - Es codificación, no cifrado real. Se usa por reversibilidad.',
            'implementacion': 'urlsafe_base64_encode() y urlsafe_base64_decode()'
        },
        {
            'nombre': 'Session Cookies',
            'uso': 'Almacenar información de sesión del usuario',
            'seguridad': 'Alta - Django las marca como HttpOnly y Secure en producción',
            'implementacion': 'Django middleware de sesiones (SESSION_COOKIE_SECURE, SESSION_COOKIE_HTTPONLY)'
        },
        {
            'nombre': 'Tokens de Recuperación',
            'uso': 'Verificación de identidad en flujo de recuperación de contraseña',
            'seguridad': 'Alta - Generados criptográficamente y expiran',
            'implementacion': 'django.contrib.auth.tokens.default_token_generator'
        },
        {
            'nombre': 'HTTPS/TLS',
            'uso': 'Encriptación en tránsito de todos los datos sensibles',
            'seguridad': 'Alta - Estándar de industria',
            'implementacion': 'Recomendado en producción (SECURE_SSL_REDIRECT=True)'
        }
    ]
    
    for enc_type in encryption_types:
        doc.add_heading(f'• {enc_type["nombre"]}', level=3)
        
        p = doc.add_paragraph()
        p.add_run('Uso: ').bold = True
        p.add_run(enc_type['uso'])
        
        p = doc.add_paragraph()
        p.add_run('Seguridad: ').bold = True
        p.add_run(enc_type['seguridad'])
        
        p = doc.add_paragraph()
        p.add_run('Implementación: ').bold = True
        p.add_run(enc_type['implementacion'])
    
    doc.add_page_break()
    
    # ========== 4. CLASES PRINCIPALES ==========
    doc.add_heading('4. Clases Principales del Sistema', level=1)
    
    doc.add_heading('4.1 Módulo de Seguridad (Usuarios)', level=2)
    
    # Clase User
    doc.add_heading('Clase: user (Heredada de AbstractUser)', level=3)
    
    user_info = [
        ('Localización', 'apps/seguridad/usuarios/models.py'),
        ('Herencia', 'Extiende django.contrib.auth.models.AbstractUser'),
        ('Base de Datos', 'Tabla: Usuarios'),
    ]
    
    for label, value in user_info:
        p = doc.add_paragraph()
        p.add_run(label + ': ').bold = True
        p.add_run(value)
    
    doc.add_heading('Atributos:', level=3)
    
    user_attrs_table = doc.add_table(rows=7, cols=3)
    user_attrs_table.style = 'Light Grid Accent 1'
    
    headers = user_attrs_table.rows[0].cells
    headers[0].text = 'Atributo'
    headers[1].text = 'Tipo'
    headers[2].text = 'Descripción'
    for cell in headers:
        set_cell_background(cell, 'D3D3D3')
    
    user_attrs = [
        ('PrimerNombre', 'CharField(50)', 'Primer nombre del usuario'),
        ('SegundoNombre', 'CharField(50)', 'Segundo nombre del usuario'),
        ('FechaRegistro', 'DateField(auto)', 'Fecha automática de registro'),
        ('HoraRegistro', 'TimeField(auto)', 'Hora automática de registro'),
        ('Rol', 'BooleanField', 'True=Administrador, False=Empleado'),
        ('email', 'EmailField', 'Email único (heredado de AbstractUser)'),
    ]
    
    for i, (attr, type_, desc) in enumerate(user_attrs, 1):
        row = user_attrs_table.rows[i].cells
        row[0].text = attr
        row[1].text = type_
        row[2].text = desc
    
    doc.add_heading('Métodos Clave:', level=3)
    
    user_methods = [
        {
            'nombre': 'rol_descripcion',
            'tipo': '@property',
            'descripcion': 'Retorna "Administrador" o "Empleado" según el valor de Rol'
        },
        {
            'nombre': 'save()',
            'tipo': 'Método',
            'descripcion': 'Sincroniza PrimerNombre con first_name y SegundoNombre con last_name. Asigna is_staff según Rol.'
        },
        {
            'nombre': '__str__()',
            'tipo': 'Método',
            'descripcion': 'Retorna el nombre completo del usuario o su username/email'
        }
    ]
    
    for method in user_methods:
        p = doc.add_paragraph()
        p.add_run(method['nombre']).bold = True
        p.add_run(f" ({method['tipo']}): ")
        p.add_run(method['descripcion'])
    
    doc.add_page_break()
    
    # ========== 4.2 CLASES DE API ==========
    doc.add_heading('4.2 Clases de API de Autenticación', level=2)
    
    api_classes = [
        {
            'nombre': 'LoginAPIView',
            'archivo': 'apps/seguridad/usuarios/auth_api.py',
            'metodo': 'POST /api/login/',
            'descripcion': 'Autentica un usuario por nombre de usuario o email y contraseña. Inicia una sesión segura.',
            'parametros': 'usuario/Usuario (str), contrasena/Contrasena (str)',
            'retorna': 'UserSerializer con datos del usuario autenticado'
        },
        {
            'nombre': 'SessionAPIView',
            'archivo': 'apps/seguridad/usuarios/auth_api.py',
            'metodo': 'GET /api/session/',
            'descripcion': 'Verifica el estado de autenticación actual y retorna datos de sesión.',
            'parametros': 'Ninguno (requiere cookie de sesión)',
            'retorna': 'authenticated (bool), user (dict), session_timeout_seconds (int)'
        },
        {
            'nombre': 'LogoutAPIView',
            'archivo': 'apps/seguridad/usuarios/auth_api.py',
            'metodo': 'POST /api/logout/',
            'descripcion': 'Cierra la sesión del usuario actual y elimina las cookies de sesión.',
            'parametros': 'Ninguno',
            'retorna': 'Mensaje de confirmación'
        },
        {
            'nombre': 'PasswordResetRequestAPIView',
            'archivo': 'apps/seguridad/usuarios/auth_api.py',
            'metodo': 'POST /api/password-reset-request/',
            'descripcion': 'Inicia el proceso de recuperación de contraseña enviando un enlace por email.',
            'parametros': 'email/Email (str)',
            'retorna': 'Mensaje de confirmación (no revela si el email existe)'
        },
        {
            'nombre': 'PasswordResetConfirmAPIView',
            'archivo': 'apps/seguridad/usuarios/auth_api.py',
            'metodo': 'POST /api/password-reset-confirm/',
            'descripcion': 'Cambia la contraseña utilizando el token de recuperación válido.',
            'parametros': 'uid (str), token (str), nueva_contrasena/Contrasena (str)',
            'retorna': 'Mensaje de éxito o error'
        }
    ]
    
    for api_class in api_classes:
        doc.add_heading(f'Clase: {api_class["nombre"]}', level=3)
        
        details = [
            ('Archivo', api_class['archivo']),
            ('Endpoint', api_class['metodo']),
            ('Descripción', api_class['descripcion']),
            ('Parámetros', api_class['parametros']),
            ('Retorna', api_class['retorna']),
        ]
        
        for label, value in details:
            p = doc.add_paragraph()
            p.add_run(label + ': ').bold = True
            p.add_run(value)
    
    doc.add_page_break()
    
    # ========== 5. MODELOS DE DATOS ==========
    doc.add_heading('5. Modelos de Datos Clave', level=1)
    
    doc.add_heading('5.1 Modelo: Factura', level=2)
    
    factura_info = [
        ('Localización', 'apps/transaccion/factura/models.py'),
        ('Tabla BD', 'Facturas'),
        ('Descripción', 'Representa una factura emitida a un cliente por servicios prestados'),
    ]
    
    for label, value in factura_info:
        p = doc.add_paragraph()
        p.add_run(label + ': ').bold = True
        p.add_run(value)
    
    doc.add_heading('Campos Principales:', level=3)
    
    factura_table = doc.add_table(rows=9, cols=3)
    factura_table.style = 'Light Grid Accent 1'
    
    headers = factura_table.rows[0].cells
    headers[0].text = 'Campo'
    headers[1].text = 'Tipo'
    headers[2].text = 'Propósito'
    for cell in headers:
        set_cell_background(cell, 'D3D3D3')
    
    factura_campos = [
        ('UsuarioId', 'ForeignKey(user)', 'Usuario que emitió la factura'),
        ('ContratoId', 'ForeignKey(Contrato)', 'Contrato asociado a la factura'),
        ('Fecha_Emision', 'DateField', 'Fecha de emisión de la factura'),
        ('Fecha_Vencimiento', 'DateField', 'Fecha en que vence el pago'),
        ('Monto_Total', 'DecimalField(18,2)', 'Monto total a pagar'),
        ('CodigoFact', 'IntegerField', 'Código único de factura'),
        ('EstadoId', 'ForeignKey(EstadoFactura)', 'Estado actual (pendiente, pagada, vencida)'),
    ]
    
    for i, (campo, tipo, proposito) in enumerate(factura_campos, 1):
        row = factura_table.rows[i].cells
        row[0].text = campo
        row[1].text = tipo
        row[2].text = proposito
    
    doc.add_heading('Método: recalcular_total()', level=3)
    doc.add_paragraph(
        'Suma todos los detalles de factura multiplicando PrecioVenta × Cantidad '
        'y actualiza el campo Monto_Total. Importante para mantener consistencia de datos.'
    )
    
    doc.add_heading('5.2 Modelo: Contrato', level=2)
    
    contrato_info = [
        ('Localización', 'apps/transaccion/contratos/models.py'),
        ('Tabla BD', 'Contratos'),
        ('Descripción', 'Acuerdo comercial entre la empresa y un cliente'),
    ]
    
    for label, value in contrato_info:
        p = doc.add_paragraph()
        p.add_run(label + ': ').bold = True
        p.add_run(value)
    
    doc.add_heading('Campos Principales:', level=3)
    
    contrato_table = doc.add_table(rows=7, cols=3)
    contrato_table.style = 'Light Grid Accent 1'
    
    headers = contrato_table.rows[0].cells
    headers[0].text = 'Campo'
    headers[1].text = 'Tipo'
    headers[2].text = 'Propósito'
    for cell in headers:
        set_cell_background(cell, 'D3D3D3')
    
    contrato_campos = [
        ('ClienteId', 'ForeignKey(Cliente)', 'Cliente del contrato'),
        ('TipoContratoId', 'ForeignKey(TipoContrato)', 'Tipo de servicio/contrato'),
        ('Fecha_Inc', 'DateField', 'Fecha de inicio'),
        ('Fecha_Fin', 'DateField', 'Fecha de vencimiento'),
        ('EstadoContrato', 'BooleanField', 'Activo/Inactivo'),
    ]
    
    for i, (campo, tipo, proposito) in enumerate(contrato_campos, 1):
        row = contrato_table.rows[i].cells
        row[0].text = campo
        row[1].text = tipo
        row[2].text = proposito
    
    doc.add_heading('5.3 Modelo: Cliente', level=2)
    
    cliente_info = [
        ('Localización', 'apps/catalogos/clientes/models.py'),
        ('Tabla BD', 'Clientes'),
        ('Descripción', 'Personas o empresas que contratan servicios'),
    ]
    
    for label, value in cliente_info:
        p = doc.add_paragraph()
        p.add_run(label + ': ').bold = True
        p.add_run(value)
    
    doc.add_heading('Validaciones Especiales:', level=3)
    
    validations = [
        ('Teléfono', 'Formato nicaraguense: +505 XXXX XXXX'),
        ('Cédula', 'Formato: 001-010190-0001A (validación mediante RegexValidator)'),
        ('Email', 'Único en el sistema'),
        ('Correo', 'Campo único'),
    ]
    
    for field, validation in validations:
        p = doc.add_paragraph()
        p.add_run(field + ': ').bold = True
        p.add_run(validation)
    
    doc.add_page_break()
    
    # ========== 5.4 AUDITORÍA ==========
    doc.add_heading('5.4 Modelo: LogAuditoria', level=2)
    
    auditoria_info = [
        ('Localización', 'apps/transaccion/auditoria/models.py'),
        ('Tabla BD', 'LogAuditoria'),
        ('Descripción', 'Registro de todos los cambios en el sistema para cumplimiento normativo'),
    ]
    
    for label, value in auditoria_info:
        p = doc.add_paragraph()
        p.add_run(label + ': ').bold = True
        p.add_run(value)
    
    doc.add_heading('Campos:', level=3)
    
    auditoria_table = doc.add_table(rows=9, cols=3)
    auditoria_table.style = 'Light Grid Accent 1'
    
    headers = auditoria_table.rows[0].cells
    headers[0].text = 'Campo'
    headers[1].text = 'Tipo'
    headers[2].text = 'Propósito'
    for cell in headers:
        set_cell_background(cell, 'D3D3D3')
    
    auditoria_campos = [
        ('IdLog', 'BigAutoField', 'ID único del log'),
        ('Tabla', 'CharField(128)', 'Tabla modificada'),
        ('Accion', 'CharField(20)', 'CREATE, UPDATE, DELETE'),
        ('ClavePrincipal', 'CharField(128)', 'ID del registro modificado'),
        ('Usuario', 'CharField(128)', 'Usuario que realizó la acción'),
        ('Host', 'CharField(128)', 'Host/IP desde donde se realizó'),
        ('Fecha', 'DateTimeField', 'Timestamp del evento'),
        ('Detalle', 'CharField(4000)', 'Descripción de cambios'),
    ]
    
    for i, (campo, tipo, proposito) in enumerate(auditoria_campos, 1):
        row = auditoria_table.rows[i].cells
        row[0].text = campo
        row[1].text = tipo
        row[2].text = proposito
    
    doc.add_page_break()
    
    # ========== 6. SERIALIZERS Y VALIDACIÓN ==========
    doc.add_heading('6. Serializers y Validación de Datos', level=1)
    
    doc.add_heading('6.1 UserSerializer', level=2)
    doc.add_paragraph(
        'Ubicación: apps/seguridad/usuarios/serializers.py'
    )
    
    doc.add_heading('Propósito:', level=3)
    doc.add_paragraph(
        'Valida y transforma los datos de usuario entre el formato JSON (API) '
        'y el modelo Django User. Implementa validaciones personalizadas.'
    )
    
    doc.add_heading('Validaciones Implementadas:', level=3)
    
    validations = [
        ('Contraseña', 'validate_Contrasena():\n- Utiliza validate_password() de Django\n- Verifica complejidad contra políticas configuradas'),
        ('Primer Nombre', 'validate_PrimerNombre():\n- Verifica que no esté vacío\n- Lo elimina de espacios en blanco'),
        ('Segundo Nombre', 'validate_SegundoNombre():\n- Verifica que no esté vacío\n- Lo limpia de espacios en blanco'),
        ('Coherencia', 'validate():\n- Si no hay username pero hay email, usa email como username\n- Verifica que la contraseña sea obligatoria en creación'),
    ]
    
    for validation_type, description in validations:
        p = doc.add_paragraph()
        p.add_run(validation_type + ': ').bold = True
        p.add_run(description)
    
    doc.add_heading('Métodos Clave:', level=3)
    
    methods = [
        ('create()', 'Crea un nuevo usuario hasheando la contraseña con set_password()'),
        ('update()', 'Actualiza usuario existente, re-hasheando contraseña si se proporciona'),
    ]
    
    for method, desc in methods:
        p = doc.add_paragraph()
        p.add_run(method + ': ').bold = True
        p.add_run(desc)
    
    doc.add_page_break()
    
    # ========== 7. MECANISMOS ADICIONALES DE SEGURIDAD ==========
    doc.add_heading('7. Mecanismos Adicionales de Seguridad', level=1)
    
    doc.add_heading('7.1 Recuperación de Contraseña Segura', level=2)
    doc.add_paragraph(
        'El flujo de recuperación implementa varias capas de seguridad:'
    )
    
    recovery_steps = [
        ('Paso 1: Solicitud', 'El usuario solicita reset ingresando su email.'),
        ('Paso 2: Validación', 'El sistema verifica que el email existe (sin revelar esto al usuario).'),
        ('Paso 3: Token', 'Se genera un token criptográfico único usando default_token_generator.'),
        ('Paso 4: Codificación', 'El UID del usuario se codifica en Base64 (urlsafe_base64_encode).'),
        ('Paso 5: Envío', 'Se envía un enlace por email con el UID y token codificados.'),
        ('Paso 6: Verificación', 'Al hacer clic, se valida que el token sea válido y no haya expirado.'),
        ('Paso 7: Cambio', 'Se valida la nueva contraseña contra los validadores de Django.'),
        ('Paso 8: Almacenamiento', 'La contraseña se hashea con PBKDF2 antes de guardarse.'),
    ]
    
    for step, description in recovery_steps:
        p = doc.add_paragraph()
        p.add_run(step + ': ').bold = True
        p.add_run(description)
    
    doc.add_heading('7.2 Control de Acceso', level=2)
    
    access_control = [
        ('LoginAPIView', 'permission_classes = [AllowAny] - Permite login sin autenticación'),
        ('SessionAPIView', 'permission_classes = [AllowAny] - Verifica estado, permitido para todos'),
        ('LogoutAPIView', 'Requiere estar autenticado (implícito por lógica)'),
        ('Otras APIs', 'Protegidas con permission_classes según roles (IsAuthenticated, IsAdminUser)'),
    ]
    
    for endpoint, control in access_control:
        p = doc.add_paragraph()
        p.add_run(endpoint + ': ').bold = True
        p.add_run(control)
    
    doc.add_heading('7.3 Protección contra Ataques Comunes', level=2)
    
    attacks = [
        ('XSS (Cross-Site Scripting)', 'Django escapa automáticamente las variables en templates'),
        ('CSRF (Cross-Site Request Forgery)', 'CsrfViewMiddleware valida tokens CSRF en POST/PUT/DELETE'),
        ('SQL Injection', 'ORM de Django utiliza queries parametrizadas por defecto'),
        ('Clickjacking', 'X-Frame-Options header configurado por SecurityMiddleware'),
        ('Fuerza Bruta', 'Las contraseñas hasheadas requieren recálculo costoso para cada intento'),
    ]
    
    for attack, protection in attacks:
        p = doc.add_paragraph()
        p.add_run(attack + ': ').bold = True
        p.add_run(protection)
    
    doc.add_page_break()
    
    # ========== 8. BUENAS PRÁCTICAS ==========
    doc.add_heading('8. Buenas Prácticas Recomendadas', level=1)
    
    doc.add_heading('8.1 Para Producción:', level=2)
    
    production_practices = [
        'Cambiar SECRET_KEY a un valor seguro y único',
        'Establecer DEBUG = False',
        'Configurar ALLOWED_HOSTS con dominios específicos',
        'Usar HTTPS/TLS en todos los endpoints',
        'Implementar rate limiting para prevenir fuerza bruta',
        'Usar variables de entorno para credenciales sensibles',
        'Implementar logging y monitoreo de intentos fallidos',
        'Realizar auditorías de seguridad periódicas',
        'Mantener Django y dependencias actualizadas'
    ]
    
    for practice in production_practices:
        doc.add_paragraph(practice, style='List Bullet')
    
    doc.add_heading('8.2 Para Desarrollo de Nuevas Funciones:', level=2)
    
    dev_practices = [
        'Siempre utilizar user.set_password() para cambiar contraseñas',
        'Implementar validaciones en serializers para garantizar integridad',
        'Usar ForeignKey con on_delete=PROTECT para datos críticos',
        'Registrar todas las operaciones sensibles en LogAuditoria',
        'Validar permisos en cada vista/API',
        'Usar transacciones de BD para operaciones complejas',
        'Escribir tests para flujos de autenticación',
        'Documentar cambios en seguridad'
    ]
    
    for practice in dev_practices:
        doc.add_paragraph(practice, style='List Bullet')
    
    doc.add_page_break()
    
    # ========== CONCLUSIÓN ==========
    doc.add_heading('Conclusión', level=1)
    
    conclusion_text = (
        'SoftFactur implementa una arquitectura de seguridad robusta aprovechando '
        'las características built-in de Django 4.2. El sistema protege las contraseñas '
        'utilizando PBKDF2 con 240,000 iteraciones, implementa controles de acceso granulares, '
        'audita todos los cambios críticos y valida todos los datos de entrada.\n\n'
        'Los puntos clave de seguridad son:\n'
    )
    
    doc.add_paragraph(conclusion_text)
    
    conclusion_points = [
        'Hash de contraseñas: PBKDF2 con SHA256 y 240,000 iteraciones',
        'Validación: Políticas de complejidad, longitud y similitud',
        'Recuperación: Proceso seguro con tokens de tiempo limitado',
        'Auditoría: Registro completo de cambios con usuario, fecha y detalles',
        'Autenticación: Sessión basada en cookies con protección CSRF',
        'Autorización: Control de roles (Administrador/Empleado)',
        'Protección: Contra XSS, SQL Injection, CSRF y Clickjacking'
    ]
    
    for point in conclusion_points:
        doc.add_paragraph(point, style='List Bullet')
    
    # Guardar documento
    output_path = r'c:\Users\Logan\Desktop\Proyectos\SoftFactur\DOCUMENTACION_SOFTFACTUR_TECNICA.docx'
    doc.save(output_path)
    
    print(f'✓ Documento creado exitosamente: {output_path}')
    return output_path

if __name__ == '__main__':
    create_softfactur_documentation()
