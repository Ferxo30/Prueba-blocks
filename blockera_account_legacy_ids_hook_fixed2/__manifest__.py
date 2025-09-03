{
    "name": "Blockera - Legacy IDs (hook fixed v2)",
    "version": "18.0.1.17",  # <- súbela
    "summary": "Campos OldCode/OldName y columnas en lista/form.",
    "author": "Blockera IT",
    "category": "Accounting/Localizations",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_account_views.xml",   # <- NUEVO
    ],
    "post_init_hook": "post_init_hook",     # Puedes dejarlo; ya no dependemos de él
    "license": "LGPL-3",
    "installable": True,
    "application": False
}
