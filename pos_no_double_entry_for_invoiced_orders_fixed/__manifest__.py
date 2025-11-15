# pos_no_double_entry_for_invoiced_orders_fixed/__manifest__.py
{
    'name': 'POS: No double entry for invoiced orders',
    'summary': 'Oculta líneas de cierre en la sesión y, ahora, asientos POSS/* para todos.',
    'version': '18.0.1.0.3',
    'author': 'ChatGPT',
    'license': 'LGPL-3',
    'website': 'https://example.com',
    'depends': ['point_of_sale', 'account'],
    'data': [
        # --- reglas de visibilidad (asientos + apuntes) ---
        'security/pos_hide_poss_rules.xml',
        'security/pos_visibility_security.xml',
        'views/res_config_settings_view.xml',
        # A FUTURO: habilitar grupo especial para ver cierres POS
        # 'security/pos_visibility_security.xml',
    ],
    # Hook para marcar histórico POSS/ en is_poss_move al instalar/actualizar
    'post_init_hook': 'set_is_poss_move_flag',
    'installable': True,
    'application': False,
}
