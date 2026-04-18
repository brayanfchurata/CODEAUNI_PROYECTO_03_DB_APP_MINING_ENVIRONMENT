class QueryLibrary:
    KPI_TOTAL_TONELADAS = """
    SELECT CAST(SUM(total_toneladas) AS DECIMAL(18,2)) AS total_toneladas
    FROM (
        SELECT SUM(toneladas_procesadas) AS total_toneladas FROM preparacion_minerales
        UNION ALL
        SELECT SUM(toneladas_procesadas) AS total_toneladas FROM extraccion_metales
        UNION ALL
        SELECT SUM(toneladas_procesadas) AS total_toneladas FROM refinacion_metales
    ) t;
    """

    KPI_COSTO_TOTAL = """
    SELECT CAST(SUM(costo_total) AS DECIMAL(18,2)) AS costo_total_usd
    FROM (
        SELECT SUM(toneladas_procesadas * costo_tonelada_usd) AS costo_total
        FROM preparacion_minerales
        UNION ALL
        SELECT SUM(costo_operacion_usd) AS costo_total
        FROM extraccion_metales
        UNION ALL
        SELECT SUM(costo_total_usd) AS costo_total
        FROM refinacion_metales
    ) t;
    """

    KPI_CONSUMO_TOTAL = """
    SELECT CAST(SUM(consumo_total) AS DECIMAL(18,2)) AS consumo_total
    FROM (
        SELECT SUM(consumo_energia_kwh) AS consumo_total FROM preparacion_minerales
        UNION ALL
        SELECT SUM(consumo_electrico_kwh) AS consumo_total FROM refinacion_metales
    ) t;
    """

    QUERY_TONELADAS_POR_ETAPA = """
    SELECT etapa, CAST(SUM(toneladas_procesadas) AS DECIMAL(18,2)) AS toneladas
    FROM (
        SELECT 'Preparacion' AS etapa, toneladas_procesadas FROM preparacion_minerales
        UNION ALL
        SELECT 'Extraccion' AS etapa, toneladas_procesadas FROM extraccion_metales
        UNION ALL
        SELECT 'Refinacion' AS etapa, toneladas_procesadas FROM refinacion_metales
    ) t
    GROUP BY etapa
    ORDER BY toneladas DESC;
    """

    QUERY_COSTO_PROMEDIO_PROCESO = """
    SELECT
        dp.proceso,
        dp.tipo_proceso,
        CAST(AVG(CASE
            WHEN dp.tipo_proceso = 'Preparacion' THEN pm.costo_tonelada_usd
            ELSE NULL
        END) AS DECIMAL(18,2)) AS costo_promedio_preparacion,
        CAST(AVG(CASE
            WHEN dp.tipo_proceso = 'Extraccion' THEN em.costo_operacion_usd
            ELSE NULL
        END) AS DECIMAL(18,2)) AS costo_promedio_extraccion,
        CAST(AVG(CASE
            WHEN dp.tipo_proceso = 'Refinacion' THEN rm.costo_total_usd
            ELSE NULL
        END) AS DECIMAL(18,2)) AS costo_promedio_refinacion
    FROM dim_procesos dp
    LEFT JOIN preparacion_minerales pm ON dp.id_proceso = pm.id_proceso
    LEFT JOIN extraccion_metales em ON dp.id_proceso = em.id_proceso
    LEFT JOIN refinacion_metales rm ON dp.id_proceso = rm.id_proceso
    GROUP BY dp.proceso, dp.tipo_proceso
    ORDER BY dp.tipo_proceso, dp.proceso;
    """

    QUERY_ALERTAS = """
    SELECT 'Preparacion' AS etapa, id, fecha, id_proceso,
           'porcentaje_recuperacion fuera de rango' AS alerta
    FROM preparacion_minerales
    WHERE porcentaje_recuperacion < 0 OR porcentaje_recuperacion > 100

    UNION ALL

    SELECT 'Preparacion', id, fecha, id_proceso,
           'tiempo_operacion_horas negativo'
    FROM preparacion_minerales
    WHERE tiempo_operacion_horas < 0

    UNION ALL

    SELECT 'Extraccion', id, fecha, id_proceso,
           'porcentaje_extraccion fuera de rango'
    FROM extraccion_metales
    WHERE porcentaje_extraccion < 0 OR porcentaje_extraccion > 100

    UNION ALL

    SELECT 'Extraccion', id, fecha, id_proceso,
           'temperatura_procesos_celcius negativa'
    FROM extraccion_metales
    WHERE temperatura_procesos_celcius < 0

    ORDER BY fecha;
    """

    QUERY_PROCESOS = """
    SELECT id_proceso, proceso, tipo_proceso
    FROM dim_procesos
    ORDER BY tipo_proceso, proceso;
    """

    QUERY_PREPARACION = """
    SELECT *
    FROM preparacion_minerales
    ORDER BY fecha DESC;
    """

    QUERY_EXTRACCION = """
    SELECT *
    FROM extraccion_metales
    ORDER BY fecha DESC;
    """

    QUERY_REFINACION = """
    SELECT *
    FROM refinacion_metales
    ORDER BY fecha DESC;
    """