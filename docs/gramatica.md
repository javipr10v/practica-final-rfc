# Gramática de RFCLang

## EBNF

```
programa → registro+ EOF
registro → 'persona' ID '{' campo+ '}'
campo    → ID '=' valor ';'
valor    → CADENA | FECHA
```

## BNF equivalente (sin repeticiones, para calcular FIRST y FOLLOW)

```
programa  → registro registros EOF
registros → registro registros | ε
registro  → PERSONA ID LLAVE_IZQ campo campos LLAVE_DER
campos    → campo campos | ε
campo     → ID ASIGNA valor PYC
valor     → CADENA | FECHA
```

## Conjuntos FIRST y FOLLOW

| No terminal | FIRST | FOLLOW |
|---|---|---|
| programa  | { PERSONA } | { $ } |
| registros | { PERSONA, ε } | { EOF } |
| registro  | { PERSONA } | { PERSONA, EOF } |
| campos    | { ID, ε } | { LLAVE_DER } |
| campo     | { ID } | { ID, LLAVE_DER } |
| valor     | { CADENA, FECHA } | { PYC } |

## Por qué es LL(1)

Las únicas reglas con alternativas son `registros`, `campos` y `valor`:

- `registros`: FIRST(registro) = { PERSONA } y FOLLOW(registros) = { EOF }. Son disjuntos.
- `campos`: FIRST(campo) = { ID } y FOLLOW(campos) = { LLAVE_DER }. Son disjuntos.
- `valor`: CADENA y FECHA son distintos.

Con un solo token de lookahead siempre se sabe qué producción usar.

## Tokens (en orden de prioridad)

| Token | Patrón |
|---|---|
| COMENTARIO | `//[^\n]*` (se descarta) |
| FECHA | `[0-9]{2}/[0-9]{2}/[0-9]{4}` |
| CADENA | `"[^"\n]*"` |
| ID | `[A-Za-z_]\w*` (si el lexema es `persona` pasa a PALABRA_RESERVADA) |
| ASIGNA, PYC | `=`  `;` |
| LLAVE_IZQ, LLAVE_DER | `{`  `}` |
| ESPACIO, SALTO | se descartan |
| ERROR | cualquier otro carácter |

## AST del ejemplo base

```
Programa
└── Registro alumno1
    ├── Campo nombre = "María Guadalupe" [CADENA]
    ├── Campo paterno = "De la Cruz" [CADENA]
    ├── Campo materno = "Núñez" [CADENA]
    └── Campo fecha_nac = 03/11/1985 [FECHA]
```
