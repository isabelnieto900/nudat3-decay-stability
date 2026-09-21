# Datos originales (NuDat 3)

**Documentación completa** (origen, URL, fechas, variables): [`docs/origen_datos.md`](../../docs/origen_datos.md)

| Campo | Valor |
|-------|--------|
| Fuente | [NNDC NuDat 3](https://www.nndc.bnl.gov/nudat3/) |
| Obtención | 2026-09-20 |
| Regla | **No modificar** estos CSV; la limpieza va a `data/processed/` |

## Archivos canónicos

| Archivo | Registros | Contenido |
|---------|-----------|-----------|
| `walletcards.csv` | 4116 | Wallet Cards: modos, \(t_{1/2}\), mass excess, isómeros |
| `nndc_nudat_data_export (10).csv` | 3150 | Chart: half-life (s) |
| `nndc_nudat_data_export (12).csv` | 4105 | Chart: Qβ−, QEC, Qβ+, BE/A, residual LDM |
| `nndc_nudat_data_export (21).csv` | 4105 | Chart: pairing gap, Qα, ΔQα |

Exports redundantes o vacíos: ver `_archive/`.

Clave de unión Chart ↔ Wallet (estado base): \((Z, N)\) con \(N = A - Z\).
