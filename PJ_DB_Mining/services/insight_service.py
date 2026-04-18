from database.repository import MiningRepository


class InsightService:
    def __init__(self, repository: MiningRepository):
        self.repository = repository

    def build_insights(self) -> list[str]:
        insights = []

        toneladas_df = self.repository.get_total_toneladas()
        costo_df = self.repository.get_total_costo()
        consumo_df = self.repository.get_total_consumo()
        costos_promedio_df = self.repository.get_costo_promedio_por_proceso()
        alertas_df = self.repository.get_alertas_calidad()

        total_toneladas = toneladas_df.iloc[0, 0] if not toneladas_df.empty else 0
        total_costo = costo_df.iloc[0, 0] if not costo_df.empty else 0
        total_consumo = consumo_df.iloc[0, 0] if not consumo_df.empty else 0

        insights.append(f"El total de toneladas procesadas es {total_toneladas}.")
        insights.append(f"El costo total acumulado estimado es USD {total_costo}.")
        insights.append(f"El consumo total acumulado registrado es {total_consumo}.")

        if not costos_promedio_df.empty:
            fila = costos_promedio_df.iloc[0]
            insights.append(
                f"El proceso '{fila['proceso']}' aparece entre los de mayor costo promedio dentro de su categoría."
            )

        if alertas_df.empty:
            insights.append("No se detectaron alertas de calidad de datos con las reglas actuales.")
        else:
            insights.append(
                f"Se detectaron {len(alertas_df.index)} alertas de calidad de datos que deben revisarse."
            )

        return insights