# PRD-001: PayTrace — por qué falló una transferencia

> **Resumen:** PayTrace ayuda a los analistas de pagos a investigar más rápido por qué una transferencia falló o quedó pendiente. Revisa el historial de eventos de la operación (trace) con reglas fijas, señala el evento que respalda el diagnóstico y recomienda el próximo paso. Si la evidencia no alcanza, indica que el caso es "no concluyente". En el MVP, las transferencias son simuladas.
>
> **Principio de producto:** PayTrace nunca nombra una causa sin citar el evento del trace que la prueba. Si la evidencia no alcanza, responde "no concluyente". Tampoco diagnostica operaciones sin fallo.

*04/11/2026 · Entregable del Módulo 1 · Sigue la plantilla de PRD de la Clase 2*

---

## 1. Contexto y problema

### La idea base
| | |
|---|---|
| **El problema hoy** | Cuando una transferencia falla o queda pendiente, el analista la rastrea a mano por varios sistemas, cada uno con su propio log y su propio ID |
| **Qué cambia con el MVP** | El analista la investiga desde un solo lugar: un historial unificado y simulado de la operación |
| **Estándar de referencia** | Los eventos simulados usan los códigos de motivo de ISO 20022, el estándar internacional de mensajes de pago (por ejemplo, `AM04` = fondos insuficientes) |

### Quién lo sufre hoy
**Para quién:** el analista de operaciones o soporte de pagos de un banco o una empresa de pagos.

**El dolor:** cuando una transferencia falla o queda pendiente, el analista toma el ID de la operación y lo sigue a mano por los logs de varios sistemas.

| Hoy | Resultado |
|---|---|
| Sigue el ID log por log (y el ID cambia entre sistemas), a veces con scripts propios | Un senior tarda ~20 min por caso y alguien nuevo, ~40 min (estimación de referencia, no medición) |
| No siempre tiene permisos para ver todos los logs | El caso se demora o se escala |
| El diagnóstico no siempre cita qué evento lo prueba | Dos analistas pueden dar causas distintas |

### Personas
| Persona | Quién es | Qué necesita |
|---|---|---|
| **Laura** | Analista senior de operaciones de pagos. Conoce los sistemas y tarda ~20 min por caso | Dejar de seguir el ID log por log y tener la causa con la evidencia a mano |
| **Nico** | Analista nuevo. No conoce todos los sistemas, no tiene permisos para ver todos los logs y tarda ~40 min por caso | Llegar a la misma causa que Laura, sin depender de su experiencia ni de pedir accesos |

### Términos
| Término | Qué significa en este PRD |
|---|---|
| **Operación** | Una transferencia simulada, con un ID único (ej.: OP-0001), un estado y un trace. Estados: **OK** (se acreditó en destino), **fallida** (la operación se rechazó: no se acredita en destino) o **pendiente** (todavía no hay un resultado final) |
| **Evento** | Un hecho del trace. Tiene ID de evento, momento, tipo, quién lo emite (origen, proveedor o banco destino) y, si es un rechazo, un código de motivo ISO 20022 |
| **Trace** | La lista de eventos de una operación, unificada y en orden |
| **Caso** | El escenario con el que se generó la operación (tabla de §3). Las reglas **no** conocen el caso: solo ven el trace |
| **Causa** | Uno de los valores de la columna "Causa" de la tabla de casos, con ese nombre exacto, o "no concluyente" |
| **Diagnóstico** | Lo que devuelve PayTrace cuando el analista lo pide. Tiene 3 campos: causa, eventos citados (por ID de evento; vacío si la causa es "no concluyente") y recomendación |
| **Conjunto de evaluación** | 25 operaciones fijas: 5 de cada caso de la tabla de §3, salvo el caso OK. Salen de un archivo de datos fijo, con IDs y horarios que no cambian entre corridas. No se generan con RF-01 |
| **Plazo de espera** | 10 minutos sin eventos nuevos desde el último evento del trace. Una transferencia inmediata se resuelve en segundos: si pasó ese tiempo sin eventos, la operación se trabó |

---

## 2. Objetivos

| ID | Objetivo | Meta | Cómo se mide | Resuelve el dolor de… |
|---|---|---|---|---|
| OBJ-1 | Investigar más rápido | **≤ 5 min** por caso (hoy ~20 min, estimación de referencia) | Mediana de 10 operaciones del conjunto de evaluación, cronometradas por una persona que no las generó, desde que busca el ID hasta que tiene el diagnóstico | Seguir el ID log por log |
| OBJ-2 | Diagnósticos con evidencia | **100 %** de los diagnósticos con causa citan exactamente un evento: el evento clave de su caso | Sobre las 20 operaciones con trace completo del conjunto de evaluación | El diagnóstico no cita qué evento lo prueba |
| OBJ-3 | No inventar | **100 %** de las operaciones con trace incompleto terminan como "no concluyente" | Sobre las 5 operaciones con trace incompleto del conjunto de evaluación | Diagnósticos sin respaldo |
| OBJ-4 | Causa correcta | **100 %** con la causa que corresponde al caso generado | Sobre las 20 operaciones con trace completo del conjunto de evaluación | Causas distintas según el analista |

---

## 3. Requerimientos funcionales

| ID | El sistema debe… | Prioridad | Cumple |
|---|---|---|---|
| RF-01 | Generar una operación simulada del caso que elija el analista | Imprescindible | Base para OBJ-1 a OBJ-4 |
| RF-02 | Listar las operaciones con su estado (OK, fallida, pendiente) | Deseable | OBJ-1 |
| RF-03 | Buscar una operación por su ID | Imprescindible | OBJ-1 |
| RF-04 | Mostrar el trace de una operación en orden cronológico | Imprescindible | OBJ-1 |
| RF-05 | Indicar como causa una de las causas de la tabla de casos, según el evento clave del trace | Imprescindible | OBJ-1 · OBJ-4 |
| RF-06 | Citar, por su ID, solo el evento clave del trace que prueba la causa | Imprescindible | OBJ-2 |
| RF-07 | Mostrar la recomendación de la tabla de casos que corresponde al trace | Imprescindible | OBJ-1 |
| RF-08 | Responder "no concluyente", sin eventos citados, cuando el trace no prueba ninguna causa y ya pasó el plazo de espera | Imprescindible | OBJ-3 |
| RF-09 | Avisar que no hay fallo cuando se pide el diagnóstico de una operación OK | Imprescindible | Principio de producto (no diagnosticar sin fallo) · se verifica con AC-10, fuera del conjunto de evaluación |

### Casos que se pueden generar (RF-01)

| Caso | Estado | Trace simulado (**evento clave** en negrita) | Causa | Recomendación |
|---|---|---|---|---|
| OK | OK | Orden enviada → débito en origen → aceptación del proveedor → **acreditación en destino** | — (no se investiga) | — |
| Fondos insuficientes | Fallida | Orden enviada → **rechazo en origen, código AM04** | fondos insuficientes | Avisar al cliente que no tenía saldo. No se debitó nada |
| Cuenta incorrecta | Fallida | Orden enviada → débito en origen → **rechazo del banco destino, código AC01** → reversa del débito | cuenta incorrecta | Pedir al cliente que verifique el CBU/CVU y confirmar que la reversa se acreditó |
| Timeout con reversa | Fallida | Orden enviada → débito en origen → envío al proveedor → **rechazo por timeout, código AB05** (el proveedor informa que el banco destino no respondió a tiempo) → reversa del débito | timeout | El débito ya se devolvió: se puede reintentar la transferencia |
| Timeout sin reversa | Fallida | Orden enviada → débito en origen → envío al proveedor → **rechazo por timeout, código AB05** (el proveedor informa que el banco destino no respondió a tiempo) | timeout | El débito todavía no se devolvió: pedir la reversa antes de reintentar. Si se reintenta antes, se cobra dos veces |
| Trace incompleto | Pendiente | Orden enviada → débito en origen → (pasaron más de 10 minutos sin ningún evento más) | no concluyente | Pedir los logs del proveedor desde el último evento conocido |

### Flujo principal (demo)

| Paso | Qué pasa |
|---|---|
| 1 | El analista genera operaciones de distintos casos (RF-01) |
| 2 | Busca una operación por su ID (RF-03) o la elige de la lista (RF-02) |
| 3 | Ve su trace en orden (RF-04) |
| 4 | Pide el diagnóstico. No es automático. Si la operación es OK, el sistema avisa que no hay fallo para investigar (RF-09) |
| 5 | Si la operación es fallida o pendiente, el analista ve la causa o el resultado "no concluyente", la evidencia cuando corresponda y la recomendación (RF-05 a RF-08) |

---

## 4. Requerimientos no funcionales

> **Cómo leer "p95":** al menos el 95 % de las mediciones tiene que dar 2 segundos o menos.
> Estos 2 segundos son lo que tarda **el sistema** en responder. Los 5 minutos de OBJ-1 son otra cosa: el tiempo de **la investigación completa** del analista, de punta a punta.

| ID | Requerimiento |
|---|---|
| RNF-01 | El diagnóstico llega en **≤ 2 s** (p95, sobre el conjunto de evaluación) |
| RNF-02 | El trace de una operación se muestra en **≤ 2 s** (p95, sobre el conjunto de evaluación) |
| RNF-03 | **0** datos personales reales: el 100 % de los datos es simulado |
| RNF-04 | Consistencia: pedir **5 veces** el diagnóstico de la misma operación da **el mismo resultado las 5 veces**, en el 100 % del conjunto de evaluación |

---

## 5. Criterios de aceptación

```gherkin
# language: es
Característica: PayTrace, criterios de aceptación del MVP

  Esquema del escenario: AC-01 (RF-01) · Generar una operación de cada caso
    Dado que el analista elige el caso "<caso>"
    Cuando genera la operación
    Entonces la operación queda con estado "<estado>"
    Y su trace tiene el evento "<evento>"
    Y el último evento del trace es "<ultimo_evento>"

    Ejemplos:
      | caso                 | estado    | evento                                  | ultimo_evento                    |
      | OK                   | OK        | acreditación en destino                 | acreditación en destino          |
      | fondos insuficientes | fallida   | rechazo en origen, código AM04          | rechazo en origen, código AM04   |
      | cuenta incorrecta    | fallida   | rechazo del banco destino, código AC01  | reversa del débito               |
      | timeout con reversa  | fallida   | rechazo por timeout, código AB05        | reversa del débito               |
      | timeout sin reversa  | fallida   | rechazo por timeout, código AB05        | rechazo por timeout, código AB05 |
      | trace incompleto     | pendiente | débito en origen                        | débito en origen                 |

  Escenario: AC-02 (RF-02) · Ver el estado de cada operación
    Dado que se generaron operaciones de los casos "OK", "fondos insuficientes" y "trace incompleto"
    Cuando el analista abre la lista
    Entonces ve esas 3 operaciones con los estados OK, fallida y pendiente

  Escenario: AC-03 (RF-03) · Buscar un ID que existe
    Dado que existe la operación "OP-0001"
    Cuando el analista busca "OP-0001"
    Entonces el sistema muestra la operación "OP-0001"

  Escenario: AC-04 (RF-03) · Buscar un ID que no existe
    Dado que no existe ninguna operación "OP-9999"
    Cuando el analista busca "OP-9999"
    Entonces el sistema muestra "Operación no encontrada"

  Escenario: AC-05 (RF-04) · Ver el trace en orden
    Dado que se generó una operación del caso "cuenta incorrecta", que tiene 4 eventos
    Cuando el analista la abre
    Entonces ve los 4 eventos, del más antiguo al más nuevo

  Esquema del escenario: AC-06 (RF-05) · Causa correcta por caso
    Dado que se generó una operación del caso "<caso>"
    Cuando el analista pide el diagnóstico
    Entonces la causa del diagnóstico es exactamente "<causa>"

    Ejemplos:
      | caso                 | causa                |
      | fondos insuficientes | fondos insuficientes |
      | cuenta incorrecta    | cuenta incorrecta    |
      | timeout con reversa  | timeout              |
      | timeout sin reversa  | timeout              |

  Esquema del escenario: AC-07 (RF-06) · Evidencia del trace
    Dado que se generó una operación del caso "<caso>"
    Cuando el analista pide el diagnóstico
    Entonces el diagnóstico cita un solo evento
    Y ese evento es el "<evento_clave>" del trace de esa operación

    Ejemplos:
      | caso                 | evento_clave                           |
      | fondos insuficientes | rechazo en origen, código AM04         |
      | cuenta incorrecta    | rechazo del banco destino, código AC01 |
      | timeout con reversa  | rechazo por timeout, código AB05       |
      | timeout sin reversa  | rechazo por timeout, código AB05       |

  Esquema del escenario: AC-08 (RF-07) · Recomendación según la causa
    Dado que se generó una operación del caso "<caso>"
    Cuando el analista pide el diagnóstico
    Entonces la recomendación es la de la tabla de casos para "<caso>"

    Ejemplos:
      | caso                 |
      | fondos insuficientes |
      | cuenta incorrecta    |
      | timeout con reversa  |
      | timeout sin reversa  |
      | trace incompleto     |

  Escenario: AC-09 (RF-08) · No concluyente
    Dado que se generó una operación del caso "trace incompleto"
    Cuando el analista pide el diagnóstico
    Entonces la causa del diagnóstico es "no concluyente"
    Y no aparece ninguna otra causa de la tabla de casos
    Y el diagnóstico no cita ningún evento

  Escenario: AC-10 (RF-09) · Operación OK
    Dado que se generó una operación del caso "OK"
    Cuando el analista pide el diagnóstico
    Entonces el sistema muestra "La operación no tiene un fallo para investigar"
    Y no se genera ningún diagnóstico

  Escenario: AC-11 (RF-03) · Buscar un ID vacío o mal escrito
    Dado que el analista escribe "op1" o deja el ID vacío
    Cuando busca
    Entonces el sistema muestra "Ingresá un ID con formato OP-0000"
    Y no hace la búsqueda

  Escenario: AC-12 (RF-08) · Operación pendiente dentro del plazo de espera
    Dado una operación pendiente cuyo último evento fue hace 2 minutos
    Cuando el analista pide el diagnóstico
    Entonces el sistema muestra "La operación sigue en curso"
    Y no se genera ningún diagnóstico
```

---

## 6. Fuera de alcance

| Queda afuera |
|---|
| Conexión con bancos, proveedores o un payment hub reales |
| Mensajes ISO 20022 completos: el MVP usa solo los códigos de motivo |
| Unir los logs reales de varios sistemas y gestionar sus permisos: el MVP parte del trace ya unido |
| Corregir o reintentar la operación: PayTrace solo diagnostica |
| Agente de IA para los casos que las reglas no cubren: queda para después del MVP |
| Login, roles y permisos |
| Paginación de la lista de operaciones (en el MVP hay unas 25) |
| Pagos con tarjeta u otros medios: solo transferencias |
| Otros casos de fallo (importe no permitido `AM02`, duplicados, antifraude, etc.) |

---

## 7. Riesgos y dependencias

### Riesgos
| Riesgo | Mitigación |
|---|---|
| Un trace real no encaja en ninguna regla | PayTrace responde "no concluyente" y no inventa una causa (RF-08 · AC-09). Para esos casos, a futuro, un agente de IA |
| Se usa mal un código ISO 20022 | El simulador usa solo 3 códigos de motivo, revisados el 04/11 contra la guía de códigos de motivo del European Payments Council: AM04 (fondos insuficientes), AC01 (la cuenta no existe en el banco destino) y AB05 (timeout del banco destino). Cualquier otro código (por ejemplo, `AM02` o `AB06`) queda fuera del MVP (ver §6) |
| Los datos simulados no se parecen a la realidad | Los casos siguen la lógica de ISO 20022. Los ~20 min de hoy son una estimación de referencia, no una medición: OBJ-1 se cumple midiendo PayTrace (≤ 5 min), sin depender de esa cifra |
| El proyecto queda demasiado grande para el curso | MVP acotado: 9 RF, 3 casos con fallo y fuera de alcance explícito |

### Dependencias
| Dependencia | Para qué |
|---|---|
| La lista oficial de códigos de motivo de ISO 20022 (External Code Sets) | Mantener alineados con el estándar los 3 códigos del simulador |
