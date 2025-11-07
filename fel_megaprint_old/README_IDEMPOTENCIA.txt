Cambios clave para evitar DTE duplicados y colgados desde POS:

1) Idempotencia real:
   - Se inserta un PRECHECK contra api/verificarDocumento con el id=uuid_factura (uuid5 de factura.id).
   - Se cambia el registro a api/registrarDocumentoUuid con RegistraDocumentoRequest (antes ...XML).
   - Fallback: si registrar no trae xml_dte, se consulta verificarDocumento por id y se parsea.

2) Timeouts HTTP:
   - Se añaden timeout=(5,30) a llamadas críticas y (5,45) para retornarPDF.

3) Persistencia antes de PDF:
   - Se hace factura.flush() antes de solicitar PDF.
   - (Recomendado) No bloquear POS por PDF; puede consultarse luego por UUID/autorización.

Versión manifest aumentada automáticamente.