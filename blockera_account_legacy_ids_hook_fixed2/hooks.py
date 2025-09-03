from odoo import api, SUPERUSER_ID

VIEW_XMLID = "blockera_account_legacy_ids_hook_fixed2.view_account_account_tree_legacy"

def _build_arch_xpath(base_arch: str) -> str:
    """
    Devuelve el bloque <data> con el XPATH correcto según si la vista base usa <list> o <tree>.
    """
    tag = "list" if "<list" in (base_arch or "") else "tree"
    return f"""
<data>
  <xpath expr="//{tag}" position="inside">
    <field name="old_code"/>
    <field name="old_name"/>
    <field name="legacy_source"/>
  </xpath>
</data>
""".strip()

def post_init_hook(env):
    # 'env' del loader -> crear Environment real con superusuario
    cr = getattr(env, "cr", None)
    api_env = api.Environment(cr, SUPERUSER_ID, {})

    View = api_env['ir.ui.view']

    # 1) Encontrar la vista base de lista de account.account
    #    En Odoo 18 puede ser type='list' o 'tree' según módulo/tema.
    base_view = View.search([
        ('model', '=', 'account.account'),
        ('inherit_id', '=', False),
        ('type', 'in', ['list', 'tree']),
    ], order="priority asc, id asc", limit=1)

    if not base_view:
        # Nada que heredar -> salir
        return

    arch_db = _build_arch_xpath(base_view.arch_db or "")

    vals = {
        'name': 'account.account.tree.legacy',
        'model': 'account.account',
        'inherit_id': base_view.id,
        'mode': 'extension',
        'arch_db': arch_db,          # ¡usar arch_db, no 'arch'!
        'type': base_view.type,      # 'list' o 'tree', según lo encontrado
    }

    # 2) Crear/actualizar nuestra vista heredada con xmlid estable
    legacy_view = api_env.ref(VIEW_XMLID, raise_if_not_found=False)
    if legacy_view:
        legacy_view.write(vals)
    else:
        legacy_view = View.create(vals)
        api_env['ir.model.data'].create({
            'name': 'view_account_account_tree_legacy',
            'module': 'blockera_account_legacy_ids_hook_fixed2',
            'model': 'ir.ui.view',
            'res_id': legacy_view.id,
            'noupdate': True,
        })
