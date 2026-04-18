from database.repository import MiningRepository


class QualityService:
    def __init__(self, repository: MiningRepository):
        self.repository = repository

    def get_alertas(self):
        return self.repository.get_alertas_calidad()

    def get_quality_summary(self) -> dict:
        alertas_df = self.get_alertas()

        total_alertas = len(alertas_df.index)

        if alertas_df.empty:
            return {
                "total_alertas": 0,
                "alertas_preparacion": 0,
                "alertas_extraccion": 0,
                "alertas_refinacion": 0,
            }

        alertas_preparacion = len(
            alertas_df[alertas_df["etapa"] == "Preparacion"]
        )
        alertas_extraccion = len(
            alertas_df[alertas_df["etapa"] == "Extraccion"]
        )
        alertas_refinacion = len(
            alertas_df[alertas_df["etapa"] == "Refinacion"]
        )

        return {
            "total_alertas": total_alertas,
            "alertas_preparacion": alertas_preparacion,
            "alertas_extraccion": alertas_extraccion,
            "alertas_refinacion": alertas_refinacion,
        }