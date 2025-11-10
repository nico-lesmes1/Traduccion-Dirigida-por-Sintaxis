
ARCHIVO_ENTRADA = "entrada.txt"

class Token:
    def __init__(self, tipo, lexema):
        self.tipo = tipo
        self.lexema = lexema
    def __repr__(self):
        return f"Token({self.tipo!r},{self.lexema!r})"

FIN = "$"
RESERVADAS = set() 

def es_letra(c):
    return c.isalpha() or c == '_'

def tokenizar(texto):
    i = 0
    n = len(texto)
    tokens = []
    while i < n:
        c = texto[i]
        if c.isspace():
            i += 1
            continue
        if es_letra(c):
            j = i
            while j < n and (texto[j].isalnum() or texto[j] == '_'):
                j += 1
            lex = texto[i:j]
            tipo = "id"
            if lex in RESERVADAS:
                tipo = lex
            tokens.append(Token(tipo, lex))
            i = j
            continue
        if c.isdigit():
            j = i
            tiene_punto = False
            while j < n and (texto[j].isdigit() or (texto[j]=='.' and not tiene_punto)):
                if texto[j] == '.':
                    tiene_punto = True
                j += 1
            lex = texto[i:j]
            tokens.append(Token("numero", lex))
            i = j
            continue
        if c in "+-*/()":
            tokens.append(Token(c, c))
            i += 1
            continue
        i += 1
    tokens.append(Token(FIN, FIN))
    return tokens


class Nodo:
    def __init__(self, etiqueta):
        self.etiqueta = etiqueta
        self.atributos = {}  
    def __repr__(self):
        return f"{self.etiqueta}"

class NodoNumero(Nodo):
    def __init__(self, lexema):
        super().__init__("Numero")
        self.lexema = lexema

class NodoIdentificador(Nodo):
    def __init__(self, nombre):
        super().__init__("Identificador")
        self.nombre = nombre

class NodoBinario(Nodo):
    def __init__(self, operador, izquierdo, derecho):
        super().__init__("Binario")
        self.operador = operador
        self.izquierdo = izquierdo
        self.derecho = derecho

class NodoExpresion(Nodo):
    def __init__(self, nodo):
        super().__init__("Expresion")
        self.nodo = nodo


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.actual = self.tokens[self.pos]
    def avanzar(self):
        if self.actual.tipo != FIN:
            self.pos += 1
            self.actual = self.tokens[self.pos]
    def aceptar(self, tipo_esperado):
        if self.actual.tipo == tipo_esperado:
            lex = self.actual.lexema
            self.avanzar()
            return lex
        raise Exception(f"Se esperaba {tipo_esperado} y se encontró {self.actual}")
    def parse_E(self):
        t = self.parse_T()
        return self.parse_Ep(t)
    def parse_Ep(self, izquierdo):
        while self.actual.tipo in ("+", "-"):
            op = self.actual.tipo
            self.avanzar()
            derecho = self.parse_T()
            izquierdo = NodoBinario(op, izquierdo, derecho)
        return NodoExpresion(izquierdo)
    def parse_T(self):
        f = self.parse_F()
        return self.parse_Tp(f)
    def parse_Tp(self, izquierdo):
        nodo = izquierdo
        while self.actual.tipo in ("*", "/"):
            op = self.actual.tipo
            self.avanzar()
            derecho = self.parse_F()
            nodo = NodoBinario(op, nodo, derecho)
        return nodo
    def parse_F(self):
        if self.actual.tipo == "(":
            self.aceptar("(")
            e = self.parse_E()
            self.aceptar(")")
            # parse_E ya devuelve NodoExpresion
            return e
        if self.actual.tipo == "numero":
            lex = self.actual.lexema
            self.avanzar()
            return NodoNumero(lex)
        if self.actual.tipo == "id":
            lex = self.actual.lexema
            self.avanzar()
            return NodoIdentificador(lex)
        raise Exception(f"Factor inesperado: {self.actual}")

class TablaSimbolos:
    def __init__(self):
        self.tabla = {}
    def registrar_uso(self, nombre, tipo=None):
        if nombre not in self.tabla:
            self.tabla[nombre] = {"tipo": tipo or "desconocido", "usos": 0}
        if tipo:
            self.tabla[nombre]["tipo"] = tipo
        self.tabla[nombre]["usos"] += 1
    def __repr__(self):
        lines = []
        for k, v in sorted(self.tabla.items()):
            lines.append(f"{k} : tipo={v['tipo']} usos={v['usos']}")
        return "\n".join(lines)

def tipo_promocionado(a, b):
    if a == b:
        return a
    if "string" in (a, b):
        return "string"
    if "float" in (a, b):
        return "float"
    return "int"

def cargar_tipos_externos(ruta):
    tipos = {}
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith("#"):
                    continue
                if ":" in linea:
                    idn, tp = linea.split(":", 1)
                    tipos[idn.strip()] = tp.strip()
    except FileNotFoundError:
        pass
    return tipos

def decorar_ast_y_tabla(nodo_raiz, tabla, tipos_externos):
    if isinstance(nodo_raiz, NodoExpresion):
        t = decorar_ast_y_tabla(nodo_raiz.nodo, tabla, tipos_externos)
        nodo_raiz.atributos["tipo"] = t
        return t
    if isinstance(nodo_raiz, NodoNumero):
        if "." in nodo_raiz.lexema:
            nodo_raiz.atributos["tipo"] = "float"
            return "float"
        nodo_raiz.atributos["tipo"] = "int"
        return "int"
    if isinstance(nodo_raiz, NodoIdentificador):
        nombre = nodo_raiz.nombre
        tipo_ext = tipos_externos.get(nombre)
        tabla.registrar_uso(nombre, tipo_ext)
        nodo_raiz.atributos["tipo"] = tabla.tabla[nombre]["tipo"]
        return nodo_raiz.atributos["tipo"]
    if isinstance(nodo_raiz, NodoBinario):
        iz = decorar_ast_y_tabla(nodo_raiz.izquierdo, tabla, tipos_externos)
        de = decorar_ast_y_tabla(nodo_raiz.derecho, tabla, tipos_externos)
        res = tipo_promocionado(iz, de)
        nodo_raiz.atributos["tipo"] = res
        return res
    return "desconocido"


def imprimir_ast_decorado_conciso(ast):
    lines = []
    def rec(n, pref=""):
        if isinstance(n, NodoExpresion):
            lines.append(f"{pref}Expresion -> tipo={n.atributos.get('tipo')}")
            rec(n.nodo, pref + "  ")
        elif isinstance(n, NodoBinario):
            lines.append(f"{pref}Binario('{n.operador}') -> tipo={n.atributos.get('tipo')}")
            rec(n.izquierdo, pref + "  ")
            rec(n.derecho, pref + "  ")
        elif isinstance(n, NodoNumero):
            lines.append(f"{pref}Numero({n.lexema}) -> tipo={n.atributos.get('tipo')}")
        elif isinstance(n, NodoIdentificador):
            lines.append(f"{pref}Id({n.nombre}) -> tipo={n.atributos.get('tipo')}")
        else:
            lines.append(f"{pref}{n}")
    rec(ast)
    return "\n".join(lines)


def main():
    try:
        with open(ARCHIVO_ENTRADA, "r", encoding="utf-8") as f:
            texto = f.read()
        archivo_usado = ARCHIVO_ENTRADA
    except FileNotFoundError:
        texto = "a + 3 * ( b - 2 )"
        archivo_usado = None

    tokens = tokenizar(texto)
    parser = Parser(tokens)
    ast = None
    try:
        ast = parser.parse_E()  
    except Exception as e:
        ast = NodoExpresion(NodoNumero("0"))

    print("AST")
    print(imprimir_ast_decorado_conciso(ast))


if __name__ == "__main__":
    main()