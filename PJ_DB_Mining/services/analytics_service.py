from database.repository import MiningRepository


class AnalyticsService:
    def __init__(self, repository: MiningRepository):
        self.repository = repository

    def get_dashboard_kpis(self) -> dict:
        toneladas_df = self.repository.get_total_toneladas()
        costo_df = self.repository.get_total_costo()
        consumo_df = self.repository.get_total_consumo()

        return {
            "total_toneladas": toneladas_df.iloc[0, 0] if not toneladas_df.empty else 0,
            "costo_total_usd": costo_df.iloc[0, 0] if not costo_df.empty else 0,
            "consumo_total": consumo_df.iloc[0, 0] if not consumo_df.empty else 0,
        }

    def get_toneladas_por_etapa(self):
        return self.repository.get_toneladas_por_etapa()

    def get_alertas_calidad(self):
        return self.repository.get_alertas_calidad()

    def get_costo_promedio_por_proceso(self):
        return self.repository.get_costo_promedio_por_proceso()