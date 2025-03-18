from sqlalchemy import text


# 📌 Query para obtener los comprobantes cargados hoy
# def comprobantes_cargados_hoy_razon_social():
#     return text("""
#         SELECT 
#           *
#         FROM 
#             CabVenta cv
#         JOIN 
#             Clientes cl ON cv.cve_CodCli = cl.cli_Cod  
#         WHERE 
#             CONVERT(DATE, cv.cve_FEmision) = CONVERT(DATE, DATEADD(DAY, -1, GETDATE()))  -- Filtrar por fecha de ayer
#         ORDER BY 
#             cv.cvecli_RazSoc ASC;
#     """)


# 📌 Query para obtener los comprobantes cargados hoy ESTE ES EL QUE VVAa
def comprobantes_cargados_hoy_razon_social():
    return text("""
        SELECT DISTINCT 
            cv.cvecli_RazSoc AS RazonSocial,  -- Razón social del cliente
            cl.cli_Email AS email,  -- Email del cliente
            v.Ven_desc AS Vendedor,  -- Nombre del vendedor
            cv.cve_CodCli AS CodigoCliente  -- Código del cliente

        FROM 
            CabVenta cv
        JOIN 
            Clientes cl ON cv.cve_CodCli = cl.cli_Cod  -- Relación entre CabVenta y Clientes
        LEFT JOIN 
            Vendedor v ON cv.cveven_Cod = v.Ven_Cod  -- Relación con Vendedor
        WHERE 
    CONVERT(DATE, cv.cve_FEmision) = CONVERT(DATE, DATEADD(DAY, -1, GETDATE()))  -- Filtrar por fecha de ayer
        ORDER BY 
            cv.cvecli_RazSoc ASC;
    """)

# 📌 Query para obtener el estado de cuenta de los últimos 45 días
def estado_cuenta_ultimos_45_dias(razon_social):
    return text(f"""
        SELECT 
            '' AS ClienteCod,
            '' AS RazonSocial,
            '' AS Comp_tipo,
            '' AS Comp_letra,
            '' AS Comp_PtoVta,
            'Saldos' AS Comp_Nro,
            'Saldo Anterior' AS CompNro,
            DATEADD(D, ISNULL(CONVERT(INT, ParamModulo.pmo_Valor) * -1, -46), GETDATE()) AS Fecha,
            DATEADD(D, ISNULL(CONVERT(INT, ParamModulo.pmo_Valor) * -1, -46), GETDATE()) AS Fecha_vto,
            '' AS CondVta_Cod,
            '' AS CondVta,
            p.VendedorCod AS VendedorCod,
            p.Vendedor AS Vendedor,
            ROUND(SUM(p.Total_Loc), 2) AS Total_Loc,
            ROUND(SUM(p.Saldo_Loc), 2) AS Saldo_Loc,
            '' AS PuntoReg_cod,
            '' AS PuntoReg,
            p.CC_Por_LugEnt AS CC_Por_LugEnt,
            '' AS LugEnt_Id,
            '' AS LugarEnt,
            p.LugarEnt_RefClienteCod AS LugarEnt_RefClienteCod,
            '0-Saldo Anterior al ' + CONVERT(VARCHAR(10), DATEADD(D, ISNULL(CONVERT(INT, ParamModulo.pmo_Valor) * -1, -46), GETDATE()), 103) AS LugarEnt_Grupo,
            p.LugarEnt_SubGrupo AS LugarEnt_SubGrupo,
            p.Habilitado
        FROM 
            _Sta_PBI_DeudoresCtaCte_Historico AS p
        LEFT JOIN 
            ParamModulo ON ParamModulo.pmo_Modulo = 'QUERIES' AND ParamModulo.pmo_Param = 'CTACTE_LUGARENTREGA'
        WHERE 
            p.Fecha < DATEADD(D, ISNULL(CONVERT(INT, ParamModulo.pmo_Valor) * -1, -46), GETDATE())
            AND p.Habilitado = 1
            AND p.RazonSocial = '{razon_social}'
        GROUP BY 
            p.LugarEnt_RefClienteCod, 
            p.LugarEnt_SubGrupo, 
            p.CC_Por_LugEnt, 
            ParamModulo.pmo_Valor, 
            p.VendedorCod, 
            p.Vendedor, 
            p.Habilitado

        UNION ALL

        SELECT 
            ClienteCod,
            RazonSocial,
            Comp_tipo,
            Comp_letra,
            Comp_PtoVta,
            Comp_Nro,
            CompNro,
            Fecha,
            Fecha_vto,
            CondVta_Cod,
            CondVta,
            VendedorCod,
            Vendedor,
            Total_Loc,
            Saldo_Loc,
            PuntoReg_cod,
            PuntoReg,
            CC_Por_LugEnt,
            LugEnt_Id,
            LugarEnt,
            LugarEnt_RefClienteCod,
            LugarEnt_Grupo,
            LugarEnt_SubGrupo,
            Habilitado
        FROM 
            _Sta_PBI_DeudoresCtaCte_Historico AS p
        LEFT JOIN 
            ParamModulo ON ParamModulo.pmo_Modulo = 'QUERIES' AND ParamModulo.pmo_Param = 'CTACTE_LUGARENTREGA'
        WHERE 
            p.Fecha >= DATEADD(D, ISNULL(CONVERT(INT, ParamModulo.pmo_Valor) * -1, -46), GETDATE())
            AND p.Habilitado = 1
            AND p.RazonSocial = '{razon_social}';
    """)
