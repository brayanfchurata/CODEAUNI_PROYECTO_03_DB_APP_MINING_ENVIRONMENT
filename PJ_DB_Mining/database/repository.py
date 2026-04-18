from database.connection import DatabaseManager
from database.queries import QueryLibrary


class MiningRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_total_toneladas(self):
        return self.db.query_df(QueryLibrary.KPI_TOTAL_TONELADAS)

    def get_total_costo(self):
        return self.db.query_df(QueryLibrary.KPI_COSTO_TOTAL)

    def get_total_consumo(self):
        return self.db.query_df(QueryLibrary.KPI_CONSUMO_TOTAL)

    def get_toneladas_por_etapa(self):
        return self.db.query_df(QueryLibrary.QUERY_TONELADAS_POR_ETAPA)

    def get_costo_promedio_por_proceso(self):
        return self.db.query_df(QueryLibrary.QUERY_COSTO_PROMEDIO_PROCESO)

    def get_alertas_calidad(self):
        return self.db.query_df(QueryLibrary.QUERY_ALERTAS)

    def get_dim_procesos(self):
        return self.db.query_df(QueryLibrary.QUERY_PROCESOS)

    def get_preparacion(self):
        return self.db.query_df(QueryLibrary.QUERY_PREPARACION)

    def get_extraccion(self):
        return self.db.query_df(QueryLibrary.QUERY_EXTRACCION)

    def get_refinacion(self):
        return self.db.query_df(QueryLibrary.QUERY_REFINACION)