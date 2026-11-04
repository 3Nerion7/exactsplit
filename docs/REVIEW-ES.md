# Guía de revisión de ExactSplit

ExactSplit reparte unidades enteras entre personas o destinos con pesos. Calcula un plan; no envía dinero ni conecta billeteras.

## Qué comprobar

1. Lee el ejemplo de diez unidades entre cuatro pesos iguales del [recorrido](WALKTHROUGH.md). Las cuotas son 2,5 cada una; dar dos a cada destino deja dos unidades. Comprueba por qué Fixed produce `[3,3,2,2]` y Rotating con cursor 2 produce `[2,2,3,3]`.
2. Revisa la tabla de pesos `[5000,5000,0]`. El tercer destino tiene peso cero. En Rotating, los otros dos alternan al conservar el cursor entre rondas. El cursor sigue al último receptor del sobrante; no avanza simplemente una posición por ronda.
3. Distingue `preview` de `commit_split`: la primera función calcula sin cambiar el cursor guardado; la segunda necesita un efecto mutable y lo cambia solamente si el cálculo termina bien.
4. Lee la limitación de Hamilton. Con pesos `[5556,3333,1111]`, subir de cuatro a cinco unidades puede quitar una al tercer destino. La app no demuestra justicia general ni evita ese caso.

## Ejecutar la comprobación

Desde la carpeta del proyecto:

```text
python scripts/verify.py --download-compiler
```

Se descarga el compilador gratuito oficial únicamente si falta en la caché local y se comprueba su hash. No se necesita tarjeta, cuenta, clave ni saldo. Si tienes un ejecutable oficial ya descargado, usa `--fe RUTA`.

El final correcto es `PASS all checks: 511 Fe runtime tests; 3 compiler pairs.`. Hay tres ejemplos diseñados para no compilar; el verificador comprueba el diagnóstico exacto y los cuenta como controles negativos, no como fallos del producto. Si sale `FAIL`, conserva ese mensaje y no lo declares aprobado.

Después de revisar y ejecutar, anota con tus palabras qué hace el cursor, qué significa conservar el total y qué limitación muestra el ejemplo de cuatro a cinco unidades. Señala cualquier parte que no entiendas. Esto no sustituye la revisión real de la persona responsable antes de presentar el concurso.
