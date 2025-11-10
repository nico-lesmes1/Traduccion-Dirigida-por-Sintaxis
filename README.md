# EDTS para suma, resta, multiplicación, división

El proyecto procesa una expresión aritmética simple compuesta por:
- operadores binarios: `+`, `-`, `*`, `/`
- paréntesis: `(`, `)`
- literales numéricos (enteros y flotantes)
- identificadores (variables)

El programa realiza las siguientes tareas principales:
1. Lector / tokenizador del texto de entrada.
2. Análisis sintáctico mediante un parser de descenso recursivo (implementación no recursiva izquierda).
3. Construcción de un AST con nodos tipados (números, identificadores, operaciones binarias, expresión).
4. Decoración del AST con información de tipo por medio de un recorrido semántico.
5. Generación de una representación concisa del AST decorado.
6. Registro de usos de identificadores en una tabla de símbolos y carga de tipos externos opcional.

## Gramática empleada

La gramática utilizada es la siguiente:

- E  -> T E'
- E' -> + T E' | - T E' | ε
- T  -> F T'
- T' -> * F T' | / F T' | ε
- F  -> ( E ) | numero | id


## Tokens reconocidos

El tokenizador `tokenizar(texto)` produce la secuencia de tokens siguiente:
- Identificadores: tipo `"id"`, lexema según `[A-Za-z_][A-Za-z0-9_]*`.
- Números: tipo `"numero"`, enteros o con punto decimal (`123` o `12.34`).
- Símbolos individuales: `+`, `-`, `*`, `/`, `(`, `)`.
- Marca de fin: token con tipo `FIN` y lexema `"$"` añadido al final.

## Atributos y decoración del AST

Se definen y propagan los siguientes atributos relevantes:
- Atributo sintetizado `"tipo"` en cada nodo (almacenado en `nodo.atributos["tipo"]`).
- En la fase de parseo se construyen nodos concretos (`NodoNumero`, `NodoIdentificador`, `NodoBinario`, `NodoExpresion`).
- La función `decorar_ast_y_tabla(nodo_raiz, tabla, tipos_externos)` recorre el AST y:
  - Para `NodoNumero`: establece el tipo `"int"` si no contiene punto decimal, o `"float"` si contiene punto decimal.
  - Para `NodoIdentificador`: consulta la tabla de tipos externos (si existe) y registra el uso en `TablaSimbolos` mediante `registrar_uso`, que crea/actualiza la entrada con un tipo (si se proporcionó) y cuenta los usos.
  - Para `NodoBinario`: decora recursivamente los operandos, obtiene sus tipos y aplica la regla de promoción vía `tipo_promocionado(a, b)` para asignar el tipo del resultado al nodo binario.
  - Para `NodoExpresion`: propaga el tipo desde su subnodo y lo almacena en `nodo_raiz.atributos["tipo"]`.

La función `tipo_promocionado` sigue una regla simple:
- Si ambos tipos coinciden, retorna dicho tipo.
- Si alguno es `"string"`, el resultado es `"string"`.
- Si alguno es `"float"`, el resultado es `"float"`.
- En cualquier otro caso, el resultado por defecto es `"int"`.


## Conjuntos de primeros, siguientes y predicción

1. Conjuntos FIRST (F)
   - FIRST(F) = { '(', numero, id }  
     - En el código: `parse_F()` comprueba `self.actual.tipo == "("`, `self.actual.tipo == "numero"` y `self.actual.tipo == "id"`; estas comprobaciones implementan exactamente la selección por FIRST(F).
   - FIRST(T) = FIRST(F) y FIRST(E) = FIRST(T)
     - En el código: `parse_T()` y `parse_E()` delegan a `parse_F()` y `parse_T()` respectivamente, por lo que la expansión inicial utiliza los mismos tokens.

2. Conjuntos FOLLOW (S)
   - FOLLOW(E) = { ')', FIN } (FIN corresponde a `$`)
   - FOLLOW(E') = FOLLOW(E) = { ')', FIN }
   - FOLLOW(T) = { '+', '-', ')', FIN }
   - FOLLOW(T') = FOLLOW(T) = { '+', '-', ')', FIN }
   - FOLLOW(F) = { '*', '/', '+', '-', ')', FIN }
   - En la implementación, las producciones epsilon (`E' -> ε`, `T' -> ε`) se materializan mediante la salida de las funciones `parse_Ep` y `parse_Tp` cuando el token actual no corresponde a ninguna entrada de FIRST de la producción recursiva (`+`, `-` para `E'`; `*`, `/` para `T'`). Esta condición implica que el token actual pertenece a FOLLOW(E') o FOLLOW(T'), y por tanto se reconoce implícitamente la condición de FOLLOW (aceptación de ε) sin construir la tabla explícita.

3. Conjuntos PREDICT (P)
   - Para cada producción A -> α, P(A->α) = FIRST(α) si α no deriva ε; si α deriva ε entonces P = FOLLOW(A).
   - Ejemplos concretos:
     - P(E -> T E') = { '(', numero, id } — en `parse_E()` el llamado a `parse_T()` se realiza cuando el token actual pertenece a este conjunto.
     - P(E' -> + T E') = { '+' } — en `parse_Ep` la iteración avanza si el token actual es `'+'`.
     - P(E' -> ε) = FOLLOW(E') = { ')', FIN } — cuando el token actual no es `'+'` ni `'-'`, la función retorna (implementando la alternativa ε).
   - En suma, el código implementa la selección de producción mediante comprobaciones directas sobre el token actual (lookahead 1), que equivalen a utilizar las entradas de PREDICT.

## Impresión del AST 

La función `imprimir_ast(ast)` genera una representación jerárquica y compacta del AST mostrando:
- La etiqueta del nodo (por ejemplo `Expresion`, `Binario`, `Numero`, `Id`).
- El lexema o nombre en nodos hoja.
- El valor del atributo `"tipo"` asignado tras la decoración.


```
Expresion -> tipo=float
  Binario('+') -> tipo=float
    Id(a) -> tipo=float
    Binario('*') -> tipo=float
      Numero(3) -> tipo=int
      Expresion -> tipo=float
        Binario('-') -> tipo=float
          Id(b) -> tipo=float
          Numero(2) -> tipo=int
```



## Ejemplo de uso

- Crear el archivo `entrada.txt` con contenido:
  ```
  a + 3 * ( b - 2 )
  ```


## Capturas de ejecución
Imagen de codigo de ejecución

<img width="345" height="86" alt="image" src="https://github.com/user-attachments/assets/a79f2642-a973-4882-a15f-7438d08e8df3" />


Resultado en consola

<img width="474" height="182" alt="image" src="https://github.com/user-attachments/assets/0a61a70e-3098-4d91-be84-ee1bc2447a1a" />



