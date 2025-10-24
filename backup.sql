--
-- PostgreSQL database dump
--

\restrict 1ykv42dMBxVxLR2Ahf4A7vCrKmNOQ5gEjZaAaYChdRevnDl9ITrM8oWfuFaZecz

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

-- Started on 2025-10-24 11:53:09

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 249 (class 1255 OID 49231)
-- Name: actualizar_fecha_modificacion(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.actualizar_fecha_modificacion() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
                BEGIN
                    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$;


ALTER FUNCTION public.actualizar_fecha_modificacion() OWNER TO postgres;

--
-- TOC entry 248 (class 1255 OID 40987)
-- Name: actualizar_fecha_modificacion_alias(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.actualizar_fecha_modificacion_alias() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.actualizar_fecha_modificacion_alias() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 237 (class 1259 OID 40965)
-- Name: alias_productos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alias_productos (
    id integer NOT NULL,
    producto_id integer NOT NULL,
    cliente_id integer NOT NULL,
    alias_1 text,
    alias_2 text,
    alias_3 text,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.alias_productos OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 40964)
-- Name: alias_productos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.alias_productos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alias_productos_id_seq OWNER TO postgres;

--
-- TOC entry 5111 (class 0 OID 0)
-- Dependencies: 236
-- Name: alias_productos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.alias_productos_id_seq OWNED BY public.alias_productos.id;


--
-- TOC entry 241 (class 1259 OID 49215)
-- Name: archivos_generados; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archivos_generados (
    id integer NOT NULL,
    nombre_archivo character varying(255) NOT NULL,
    tipo_archivo character varying(10) NOT NULL,
    ruta_archivo text NOT NULL,
    fecha_generacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    cantidad_pedidos integer DEFAULT 0,
    pedidos_ids integer[],
    estado character varying(20) DEFAULT 'generado'::character varying,
    "tamaño_bytes" bigint,
    usuario_generacion character varying(100),
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.archivos_generados OWNER TO postgres;

--
-- TOC entry 240 (class 1259 OID 49214)
-- Name: archivos_generados_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.archivos_generados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.archivos_generados_id_seq OWNER TO postgres;

--
-- TOC entry 5112 (class 0 OID 0)
-- Dependencies: 240
-- Name: archivos_generados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.archivos_generados_id_seq OWNED BY public.archivos_generados.id;


--
-- TOC entry 231 (class 1259 OID 24640)
-- Name: bodegas_producto_por_cliente; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bodegas_producto_por_cliente (
    id integer NOT NULL,
    cliente_id integer NOT NULL,
    producto_id integer NOT NULL,
    bodega character varying(50) NOT NULL
);


ALTER TABLE public.bodegas_producto_por_cliente OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 24639)
-- Name: bodegas_producto_por_cliente_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bodegas_producto_por_cliente_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bodegas_producto_por_cliente_id_seq OWNER TO postgres;

--
-- TOC entry 5113 (class 0 OID 0)
-- Dependencies: 230
-- Name: bodegas_producto_por_cliente_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bodegas_producto_por_cliente_id_seq OWNED BY public.bodegas_producto_por_cliente.id;


--
-- TOC entry 233 (class 1259 OID 24660)
-- Name: bodegas_producto_por_sucursal; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bodegas_producto_por_sucursal (
    id integer NOT NULL,
    sucursal_id integer NOT NULL,
    producto_id integer NOT NULL,
    bodega character varying(50) NOT NULL
);


ALTER TABLE public.bodegas_producto_por_sucursal OWNER TO postgres;

--
-- TOC entry 232 (class 1259 OID 24659)
-- Name: bodegas_producto_por_sucursal_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bodegas_producto_por_sucursal_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bodegas_producto_por_sucursal_id_seq OWNER TO postgres;

--
-- TOC entry 5114 (class 0 OID 0)
-- Dependencies: 232
-- Name: bodegas_producto_por_sucursal_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bodegas_producto_por_sucursal_id_seq OWNED BY public.bodegas_producto_por_sucursal.id;


--
-- TOC entry 225 (class 1259 OID 24577)
-- Name: clientes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.clientes (
    id integer NOT NULL,
    nombre text NOT NULL,
    ruc character varying(13) NOT NULL,
    usa_bodega_por_sucursal boolean DEFAULT false NOT NULL,
    alias_por_sucursal boolean DEFAULT false NOT NULL,
    alias_por_producto boolean DEFAULT false NOT NULL,
    ruc_por_sucursal boolean DEFAULT false NOT NULL
);


ALTER TABLE public.clientes OWNER TO postgres;

--
-- TOC entry 5115 (class 0 OID 0)
-- Dependencies: 225
-- Name: COLUMN clientes.ruc_por_sucursal; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.clientes.ruc_por_sucursal IS 'Si TRUE, cada sucursal tiene su propio RUC. Si FALSE, se usa el RUC del cliente para todas las sucursales.';


--
-- TOC entry 224 (class 1259 OID 24576)
-- Name: clientes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.clientes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.clientes_id_seq OWNER TO postgres;

--
-- TOC entry 5116 (class 0 OID 0)
-- Dependencies: 224
-- Name: clientes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.clientes_id_seq OWNED BY public.clientes.id;


--
-- TOC entry 235 (class 1259 OID 32774)
-- Name: configuracion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.configuracion (
    id integer NOT NULL,
    clave character varying(50) NOT NULL,
    valor text NOT NULL,
    descripcion text,
    fecha_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.configuracion OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 32773)
-- Name: configuracion_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.configuracion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.configuracion_id_seq OWNER TO postgres;

--
-- TOC entry 5117 (class 0 OID 0)
-- Dependencies: 234
-- Name: configuracion_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.configuracion_id_seq OWNED BY public.configuracion.id;


--
-- TOC entry 245 (class 1259 OID 82002)
-- Name: correos_procesados; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.correos_procesados (
    id integer NOT NULL,
    uid integer NOT NULL,
    fecha_procesado timestamp without time zone DEFAULT now(),
    remitente character varying(255),
    asunto text,
    procesado_exitosamente boolean DEFAULT true,
    observaciones text
);


ALTER TABLE public.correos_procesados OWNER TO postgres;

--
-- TOC entry 5118 (class 0 OID 0)
-- Dependencies: 245
-- Name: TABLE correos_procesados; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.correos_procesados IS 'Registra UIDs de correos procesados para evitar duplicados y recuperar correos perdidos';


--
-- TOC entry 5119 (class 0 OID 0)
-- Dependencies: 245
-- Name: COLUMN correos_procesados.uid; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.correos_procesados.uid IS 'UID único del correo en el servidor IMAP';


--
-- TOC entry 5120 (class 0 OID 0)
-- Dependencies: 245
-- Name: COLUMN correos_procesados.procesado_exitosamente; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.correos_procesados.procesado_exitosamente IS 'Indica si el correo se procesó correctamente o tuvo errores';


--
-- TOC entry 5121 (class 0 OID 0)
-- Dependencies: 245
-- Name: COLUMN correos_procesados.observaciones; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.correos_procesados.observaciones IS 'Notas sobre el procesamiento (errores, etc.)';


--
-- TOC entry 244 (class 1259 OID 82001)
-- Name: correos_procesados_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.correos_procesados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.correos_procesados_id_seq OWNER TO postgres;

--
-- TOC entry 5122 (class 0 OID 0)
-- Dependencies: 244
-- Name: correos_procesados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.correos_procesados_id_seq OWNED BY public.correos_procesados.id;


--
-- TOC entry 222 (class 1259 OID 16397)
-- Name: pedido_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pedido_items (
    id integer NOT NULL,
    pedido_id integer,
    descripcion text NOT NULL,
    sku character varying(50),
    bodega character varying(50),
    cantidad integer NOT NULL,
    producto_id integer
);


ALTER TABLE public.pedido_items OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16396)
-- Name: pedido_items_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pedido_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pedido_items_id_seq OWNER TO postgres;

--
-- TOC entry 5123 (class 0 OID 0)
-- Dependencies: 221
-- Name: pedido_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pedido_items_id_seq OWNED BY public.pedido_items.id;


--
-- TOC entry 223 (class 1259 OID 16413)
-- Name: pedidos_numero_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pedidos_numero_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pedidos_numero_seq OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 16390)
-- Name: pedidos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pedidos (
    id integer NOT NULL,
    numero_pedido integer DEFAULT nextval('public.pedidos_numero_seq'::regclass) NOT NULL,
    fecha timestamp without time zone NOT NULL,
    pdf_filename text,
    email_uid bigint,
    email_from text,
    email_subject text,
    sucursal text,
    cliente_id integer,
    sucursal_id integer,
    estado character varying(20) DEFAULT 'por_procesar'::character varying,
    orden_compra character varying(50),
    CONSTRAINT chk_estado CHECK (((estado)::text = ANY ((ARRAY['por_procesar'::character varying, 'procesado'::character varying, 'con_errores'::character varying])::text[])))
);


ALTER TABLE public.pedidos OWNER TO postgres;

--
-- TOC entry 5124 (class 0 OID 0)
-- Dependencies: 220
-- Name: COLUMN pedidos.orden_compra; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.pedidos.orden_compra IS 'NÃºmero de orden de compra extraÃ­do del PDF (ej. OS-0-0-4887)';


--
-- TOC entry 219 (class 1259 OID 16389)
-- Name: pedidos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pedidos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pedidos_id_seq OWNER TO postgres;

--
-- TOC entry 5125 (class 0 OID 0)
-- Dependencies: 219
-- Name: pedidos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pedidos_id_seq OWNED BY public.pedidos.id;


--
-- TOC entry 247 (class 1259 OID 106552)
-- Name: producto_alias; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.producto_alias (
    id integer NOT NULL,
    producto_id integer NOT NULL,
    cliente_id integer NOT NULL,
    alias text NOT NULL,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.producto_alias OWNER TO postgres;

--
-- TOC entry 246 (class 1259 OID 106551)
-- Name: producto_alias_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.producto_alias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.producto_alias_id_seq OWNER TO postgres;

--
-- TOC entry 5126 (class 0 OID 0)
-- Dependencies: 246
-- Name: producto_alias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.producto_alias_id_seq OWNED BY public.producto_alias.id;


--
-- TOC entry 229 (class 1259 OID 24607)
-- Name: productos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.productos (
    id integer NOT NULL,
    sku character varying(50) NOT NULL,
    nombre text NOT NULL,
    activo boolean DEFAULT true NOT NULL
);


ALTER TABLE public.productos OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 24606)
-- Name: productos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.productos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.productos_id_seq OWNER TO postgres;

--
-- TOC entry 5127 (class 0 OID 0)
-- Dependencies: 228
-- Name: productos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.productos_id_seq OWNED BY public.productos.id;


--
-- TOC entry 227 (class 1259 OID 24590)
-- Name: sucursales; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sucursales (
    id integer NOT NULL,
    cliente_id integer NOT NULL,
    alias text,
    nombre text NOT NULL,
    encargado text,
    direccion text,
    activo boolean DEFAULT true NOT NULL,
    almacen character varying(10),
    ruc character varying(13),
    ciudad character varying(100)
);


ALTER TABLE public.sucursales OWNER TO postgres;

--
-- TOC entry 5128 (class 0 OID 0)
-- Dependencies: 227
-- Name: COLUMN sucursales.ruc; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.sucursales.ruc IS 'RUC especÃ­fico de la sucursal. Solo se usa si el cliente tiene ruc_por_sucursal = TRUE.';


--
-- TOC entry 5129 (class 0 OID 0)
-- Dependencies: 227
-- Name: COLUMN sucursales.ciudad; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.sucursales.ciudad IS 'Ciudad donde se encuentra ubicada la sucursal.';


--
-- TOC entry 226 (class 1259 OID 24589)
-- Name: sucursales_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sucursales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sucursales_id_seq OWNER TO postgres;

--
-- TOC entry 5130 (class 0 OID 0)
-- Dependencies: 226
-- Name: sucursales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sucursales_id_seq OWNED BY public.sucursales.id;


--
-- TOC entry 243 (class 1259 OID 81985)
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(255) NOT NULL,
    nombre_completo character varying(100),
    email character varying(100),
    activo boolean DEFAULT true,
    fecha_creacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso timestamp without time zone
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- TOC entry 242 (class 1259 OID 81984)
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO postgres;

--
-- TOC entry 5131 (class 0 OID 0)
-- Dependencies: 242
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- TOC entry 239 (class 1259 OID 49193)
-- Name: vista_estadisticas_pedidos; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.vista_estadisticas_pedidos AS
 SELECT estado,
    count(*) AS cantidad,
    min(fecha) AS fecha_mas_antigua,
    max(fecha) AS fecha_mas_reciente
   FROM public.pedidos
  GROUP BY estado;


ALTER VIEW public.vista_estadisticas_pedidos OWNER TO postgres;

--
-- TOC entry 238 (class 1259 OID 49188)
-- Name: vista_pedidos_completa; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.vista_pedidos_completa AS
 SELECT p.id,
    p.numero_pedido,
    p.fecha,
    p.sucursal,
    p.estado,
    c.nombre AS cliente_nombre,
    s.nombre AS sucursal_nombre,
    count(pi.id) AS total_items
   FROM (((public.pedidos p
     LEFT JOIN public.clientes c ON ((p.cliente_id = c.id)))
     LEFT JOIN public.sucursales s ON ((p.sucursal_id = s.id)))
     LEFT JOIN public.pedido_items pi ON ((p.id = pi.pedido_id)))
  GROUP BY p.id, p.numero_pedido, p.fecha, p.sucursal, p.estado, c.nombre, s.nombre;


ALTER VIEW public.vista_pedidos_completa OWNER TO postgres;

--
-- TOC entry 4832 (class 2604 OID 40968)
-- Name: alias_productos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alias_productos ALTER COLUMN id SET DEFAULT nextval('public.alias_productos_id_seq'::regclass);


--
-- TOC entry 4835 (class 2604 OID 49218)
-- Name: archivos_generados id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archivos_generados ALTER COLUMN id SET DEFAULT nextval('public.archivos_generados_id_seq'::regclass);


--
-- TOC entry 4828 (class 2604 OID 24643)
-- Name: bodegas_producto_por_cliente id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bodegas_producto_por_cliente ALTER COLUMN id SET DEFAULT nextval('public.bodegas_producto_por_cliente_id_seq'::regclass);


--
-- TOC entry 4829 (class 2604 OID 24663)
-- Name: bodegas_producto_por_sucursal id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bodegas_producto_por_sucursal ALTER COLUMN id SET DEFAULT nextval('public.bodegas_producto_por_sucursal_id_seq'::regclass);


--
-- TOC entry 4819 (class 2604 OID 24580)
-- Name: clientes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clientes ALTER COLUMN id SET DEFAULT nextval('public.clientes_id_seq'::regclass);


--
-- TOC entry 4830 (class 2604 OID 32777)
-- Name: configuracion id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configuracion ALTER COLUMN id SET DEFAULT nextval('public.configuracion_id_seq'::regclass);


--
-- TOC entry 4844 (class 2604 OID 82005)
-- Name: correos_procesados id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correos_procesados ALTER COLUMN id SET DEFAULT nextval('public.correos_procesados_id_seq'::regclass);


--
-- TOC entry 4818 (class 2604 OID 16400)
-- Name: pedido_items id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedido_items ALTER COLUMN id SET DEFAULT nextval('public.pedido_items_id_seq'::regclass);


--
-- TOC entry 4815 (class 2604 OID 16393)
-- Name: pedidos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedidos ALTER COLUMN id SET DEFAULT nextval('public.pedidos_id_seq'::regclass);


--
-- TOC entry 4847 (class 2604 OID 106555)
-- Name: producto_alias id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.producto_alias ALTER COLUMN id SET DEFAULT nextval('public.producto_alias_id_seq'::regclass);


--
-- TOC entry 4826 (class 2604 OID 24610)
-- Name: productos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.productos ALTER COLUMN id SET DEFAULT nextval('public.productos_id_seq'::regclass);


--
-- TOC entry 4824 (class 2604 OID 24593)
-- Name: sucursales id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sucursales ALTER COLUMN id SET DEFAULT nextval('public.sucursales_id_seq'::regclass);


--
-- TOC entry 4841 (class 2604 OID 81988)
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- TOC entry 5097 (class 0 OID 40965)
-- Dependencies: 237
-- Data for Name: alias_productos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alias_productos (id, producto_id, cliente_id, alias_1, alias_2, alias_3, fecha_creacion, fecha_actualizacion) FROM stdin;
\.


--
-- TOC entry 5099 (class 0 OID 49215)
-- Dependencies: 241
-- Data for Name: archivos_generados; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.archivos_generados (id, nombre_archivo, tipo_archivo, ruta_archivo, fecha_generacion, cantidad_pedidos, pedidos_ids, estado, "tamaño_bytes", usuario_generacion, fecha_creacion, fecha_actualizacion) FROM stdin;
1	ODRF_20250923_180435.txt	ODRF	ODRF_20250923_180435.txt	2025-09-23 18:04:36.326425	9	{40,41,43,44,45,47,48,52,53}	generado	1016	\N	2025-09-23 18:04:36.326425	2025-09-23 18:04:36.326425
2	DRF1_20250923_180435.txt	DRF1	DRF1_20250923_180435.txt	2025-09-23 18:04:36.375016	9	{40,41,43,44,45,47,48,52,53}	generado	8472	\N	2025-09-23 18:04:36.375016	2025-09-23 18:04:36.375016
\.


--
-- TOC entry 5091 (class 0 OID 24640)
-- Dependencies: 231
-- Data for Name: bodegas_producto_por_cliente; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bodegas_producto_por_cliente (id, cliente_id, producto_id, bodega) FROM stdin;
19402	1	2923	01
19403	1	3043	01
19404	1	2989	07
19405	1	3042	07
19406	1	3014	07
19407	1	2934	01
19408	1	3051	01
19409	1	2990	07
19410	1	2984	07
19411	1	2947	01
19412	1	2959	01
19413	1	2958	01
19414	1	2919	01
19415	1	3076	01
19416	1	3028	07
19417	1	3058	01
19418	1	3059	01
19419	1	2991	07
19420	1	3030	07
19421	1	2968	07
19422	1	2967	07
19423	1	3052	01
19424	1	2953	01
19425	1	2951	01
19426	1	2952	01
19427	1	2905	01
19428	1	2945	01
19429	1	2914	01
19430	1	2969	07
19431	1	2992	07
19432	1	3087	07
19433	1	2993	07
19434	1	3031	07
19435	1	3032	01
19436	1	2894	01
19437	1	2890	01
19438	1	2891	01
19439	1	3045	01
19440	1	2927	01
19441	1	3088	07
19442	1	2962	07
19443	1	3037	07
19444	1	2994	07
19445	1	2971	07
19446	1	2995	07
19447	1	2964	07
19448	1	3056	01
19449	1	3078	01
19450	1	2896	01
19451	1	2979	07
19452	1	2996	07
19453	1	2888	01
19454	1	2976	07
19455	1	3047	01
19456	1	2940	01
19457	1	3046	01
19458	1	3071	01
19459	1	3055	01
19460	1	2957	01
19461	1	3049	01
19462	1	3089	01
19463	1	2928	01
19464	1	3079	01
19465	1	3064	01
19466	1	3029	07
19467	1	2903	01
19468	1	2925	01
19469	1	3060	01
19470	1	3091	07
19471	1	2997	07
19472	1	2998	07
19473	1	2999	07
19474	1	2980	07
19475	1	2892	01
19476	1	2935	01
19477	1	2949	01
19478	1	2966	07
19479	1	3036	07
19480	1	2944	01
19481	1	2911	01
19482	1	2895	01
19483	1	2912	01
19484	1	2942	01
19485	1	3000	07
19486	1	2983	07
19487	1	2909	01
19488	1	2908	01
19489	1	3084	01
19490	1	2907	01
19491	1	3085	01
19492	1	2910	01
19493	1	2943	01
19494	1	2937	01
19495	1	2936	01
19496	1	2887	01
19497	1	2889	01
19498	1	2883	01
19499	1	2884	01
19500	1	2885	01
19501	1	2886	01
19502	1	2948	01
19503	1	3001	07
19504	1	3083	01
19505	1	3053	01
19506	1	3050	01
19507	1	2946	01
19508	1	2965	07
19509	1	3038	07
19510	1	2922	01
19511	1	2921	01
19512	1	2941	01
19513	1	3073	01
19514	1	3048	01
19515	1	2906	01
19516	1	3044	01
19517	1	2970	07
19518	1	3021	07
19519	1	3075	07
19520	1	3074	07
19521	1	3026	07
19522	1	3027	07
19523	1	3023	07
19524	1	3024	07
19525	1	3022	07
19526	1	3025	07
19527	1	3039	07
19528	1	3065	07
19529	1	2988	07
19530	1	2950	01
19531	1	2985	07
19532	1	3057	01
19533	1	3040	07
19534	1	3034	07
19535	1	2917	01
19536	1	2893	01
19537	1	3061	01
19538	1	2954	01
19539	1	3066	01
19540	1	3012	07
19541	1	3011	07
19542	1	3081	07
19543	1	2933	01
19544	1	2902	01
19545	1	3002	07
19546	1	2960	01
19547	1	3003	07
19548	1	3041	07
19549	1	2880	01
19550	1	2913	01
19551	1	2956	01
19552	1	2955	01
19553	1	3086	07
19554	1	3068	01
19555	1	3067	01
19556	1	3063	01
19557	1	3004	07
19558	1	3070	07
19559	1	3013	07
19560	1	2961	01
19561	1	2929	01
19562	1	2901	01
19563	1	3005	07
19564	1	2986	07
19565	1	2900	01
19566	1	2926	01
19567	1	2920	01
19568	1	2972	07
19569	1	2974	07
19570	1	2975	07
19571	1	2973	07
19572	1	2963	07
19573	1	3082	07
19574	1	2987	07
19575	1	3033	07
19576	1	3077	07
19577	1	2977	07
19578	1	2978	07
19579	1	2982	07
19580	1	2879	01
19581	1	2898	01
19582	1	2897	01
19583	1	2899	01
19584	1	3072	01
19585	1	3035	07
19586	1	3016	07
19587	1	3017	07
19588	1	3018	01
19589	1	3020	07
19590	1	3019	07
19591	1	2930	01
19592	1	3015	07
19593	1	3062	01
19594	1	2938	01
19595	1	2915	01
19596	1	2916	01
19597	1	3006	07
19598	1	3007	07
19599	1	3008	07
19600	1	3009	07
19601	1	3080	07
19602	1	2918	01
19603	1	2881	01
19604	1	2882	01
19605	1	3054	01
19606	1	3069	01
19607	1	3090	01
19608	1	2924	01
19609	1	2931	01
19610	1	2981	07
19611	1	2932	01
19612	1	2904	01
19613	1	2939	01
19614	1	3010	07
\.


--
-- TOC entry 5093 (class 0 OID 24660)
-- Dependencies: 233
-- Data for Name: bodegas_producto_por_sucursal; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bodegas_producto_por_sucursal (id, sucursal_id, producto_id, bodega) FROM stdin;
\.


--
-- TOC entry 5085 (class 0 OID 24577)
-- Dependencies: 225
-- Data for Name: clientes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.clientes (id, nombre, ruc, usa_bodega_por_sucursal, alias_por_sucursal, alias_por_producto, ruc_por_sucursal) FROM stdin;
1	Roldan	1790012345002	f	t	t	t
2	Marcimex	1790012342001	t	f	f	f
\.


--
-- TOC entry 5095 (class 0 OID 32774)
-- Dependencies: 235
-- Data for Name: configuracion; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.configuracion (id, clave, valor, descripcion, fecha_actualizacion) FROM stdin;
1	numero_pedido_inicial	1000	Número inicial para generar números de pedido secuenciales	2025-10-24 09:45:12.790416
\.


--
-- TOC entry 5103 (class 0 OID 82002)
-- Dependencies: 245
-- Data for Name: correos_procesados; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.correos_procesados (id, uid, fecha_procesado, remitente, asunto, procesado_exitosamente, observaciones) FROM stdin;
1	12345	2025-10-06 14:38:11.420233	test@ejemplo.com	Correo de prueba	t	Prueba del sistema
2	12346	2025-10-06 14:38:11.721168	error@ejemplo.com	Correo con error	f	Error de prueba
\.


--
-- TOC entry 5082 (class 0 OID 16397)
-- Dependencies: 222
-- Data for Name: pedido_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pedido_items (id, pedido_id, descripcion, sku, bodega, cantidad, producto_id) FROM stdin;
6669	384	TE FRUTOS ROJOS	COM5505	01	2	\N
6670	384	VASOS TERMICOS 6 ONZ.	COM5468	01	3	\N
6671	384	VASOS PLASTICOS 7 ONZ.	COM5220	01	2	\N
6672	384	SERVILLETAS	ABS0112	01	2	\N
6673	384	CAFE BUEN DIA 170 GR	COM5247	01	1	\N
6674	384	AZUCAR DE 2 KG	COM5367	01	1	\N
6675	384	RESALTADOR ROSADO	OFI0065	07	1	\N
6676	384	REPUESTOS DE CUCHILLAS (ESTILETES)	OFI0125	07	1	\N
6677	384	TIJERAS	OFI0231	07	1	\N
6678	384	ESFERO AZUL	OFI0188	07	10	\N
6679	384	MARCADOR PERMANENTE PUNTA FINA NEGRO	OFI0268	07	6	\N
6680	384	RESMAS DE PAPEL BOND A4	OFI0031	07	4	\N
6681	384	PASTILLA BAÑO TANQUE	\N	\N	2	\N
6682	384	ROLLO DE TOALLAS CAFÉ PARA MANOS 150 METROS	ABS0482	01	1	\N
6683	384	FUNDAS BASURA JUMBO NEGRAS 38*55 PAQ 10	\N	\N	1	\N
6684	384	FILM STRECH PEQUEÑO	OFI0127	07	3	\N
6685	384	ESTILETES	OFI0069	07	3	\N
6686	384	JABON DESENGRASANTE DE MANOS (PARA MECANICA)	COM5577	01	1	\N
6687	384	DESINFECTANTE DE PISOS GALON	QUI1176	01	1	\N
6688	384	PEGAMENTO BONDER	\N	\N	4	\N
6689	384	CINTA AISLANTE ELECTRICA	COM5401	01	4	\N
6690	384	MARCADORES PARA VIDRIO CAJA DE MARCADORES DE COLORES POR 10 UNIDADES\nPARA VIDRIO	\N	\N	12	\N
6691	384	JABON LIQUIDO GALON	\N	\N	1	\N
6692	384	PROTECTORES AUDITIVOS CON CORDON	\N	\N	6	\N
6693	384	MICROFIBRAS	TTS0232	01	8	\N
6694	384	REPUESTOS DE MOPAS BLANCAS	\N	\N	4	\N
6695	384	ESCOBA ZULY	COM5397	01	3	\N
6696	384	AMBIENTALES SPRAY GLADE EN SPRAY PRIMAVERA FRUTAL	\N	\N	2	\N
6697	384	GUANTES PALMA AZUL G-40 TALLA 7	COM5621	01	10	\N
6698	384	FUNDAS BASURA BLANCAS PERFUMADAS	COM5256	01	3	\N
6699	384	FUNDA DINA 6 TIPO CAMISA	COM5103	01	4	\N
6700	384	DETERGENTE	COM5404	01	4	\N
6701	384	GUANTES NITRILO TALLA M	COM5488	01	3	\N
6702	385	RESMAS DE PAPEL BOND A4	OFI0031	07	10	\N
6703	385	RESALTADOR AMARILLO	OFI0063	07	3	\N
6704	385	ESFERO AZUL	OFI0188	07	10	\N
6705	385	LAPIZ	OFI0045	07	5	\N
6706	385	CORRECTOR	OFI0077	07	3	\N
6707	385	TIJERAS	OFI0231	07	3	\N
6708	385	CLIPS PEQUEÑOS	OFI0051	07	9	\N
6709	385	CLIPS MARIPOSA	OFI0172	07	4	\N
6710	385	SEPARADOR DE HOJAS	OFI0089	07	3	\N
6711	385	CINTA SCOTCH PEQUEÑA	OFI0040	07	8	\N
6712	385	CINTA DE EMBALAJE PEQUEÑA 200 MTRS	OFI0028	07	5	\N
6713	385	FILM STRECH MEDIANO	OFI0260	07	2	\N
6714	385	MARCADOR PARA PIZARRA AZUL	OFI0274	07	4	\N
6715	385	MARCADOR PARA PIZARRA NEGRO	OFI0275	07	4	\N
6716	385	CAJA DE VINCHAS PARA CARPETAS	OFI0242	07	2	\N
6717	385	SERVILLETAS	ABS0112	01	6	\N
6718	385	REMOVEDOR DE AZUCAR	COM5424	01	5	\N
6719	385	AZUCAR DE 2 KG	COM5367	01	4	\N
6720	385	CAFE DE PASAR MINERVA 1KG	\N	\N	4	\N
6721	385	TE MANZANILLA	COM5320	01	1	\N
6722	385	TE MANZANILLA MIEL	COM5598	01	2	\N
6723	385	TE FRUTOS ROJOS	COM5505	01	2	\N
6724	385	CARPETA DE MANILA (PAQX10)	OFI0319	07	9	\N
6725	385	MARCADOR PERMANENTE PUNTA GRUESA NEGRO	\N	\N	3	\N
6726	385	FILM STRECH PEQUEÑO	OFI0127	07	4	\N
6727	385	FILM STRECH GRANDE	OFI0311	07	2	\N
6728	385	CLORO GALON	\N	\N	3	\N
6729	385	DESINFECTANTE DE PISOS GALON	QUI1176	01	4	\N
6730	385	FUNDAS BASURA INDUSTRIAL NEGRAS 30*36 PAQ 10	\N	\N	5	\N
6731	385	FUNDAS BASURA JUMBO NEGRAS 38*55 PAQ 10	\N	\N	10	\N
6732	385	PAPEL HIGIENICO JUMBO 500 METROS	ABS0373	01	10	\N
6733	385	PAPEL HIGIENICO PEQUEÑO	\N	\N	1	\N
6734	385	ROLLO DE TOALLAS CAFÉ PARA MANOS 150 METROS	ABS0482	01	10	\N
6735	385	MICROFIBRAS PEQUEÑAS (PAQX3)	COM5507	01	5	\N
6736	385	LAVAVAJILLA CREMA 950 GR	\N	\N	2	\N
6737	385	PROTECTOR DE HOJAS	OFI0252	07	9	\N
6738	385	CERA PARA PISOS CERAMICA	QUI0090	01	2	\N
6739	385	BROCHA #2	\N	\N	2	\N
6740	385	ESPATULA	\N	\N	3	\N
6741	385	FUNDAS BASURA BLANCAS	\N	\N	10	\N
6742	385	CERA PARA PISO FLOTANTE LIQUIDO PARA LIMPIAR PISO FLOTANTE	\N	\N	2	\N
6743	385	LUSTRE PARA PISOS # 8	\N	\N	3	\N
6744	385	GUANTES NITRILO TALLA M	COM5488	01	2	\N
6745	385	GUANTES NITRILO TALLA L	COM5489	01	2	\N
6746	385	DESENGRASANTE PARA PISOS	QUI0123	01	4	\N
6747	385	JABON DE MANOS	QUI0572	01	2	\N
6748	385	ALCOHOL	QUI0080	01	3	\N
6749	385	DETERGENTE	COM5404	01	4	\N
6750	385	JABON LIQUIDO 500 ML	QUI0212	01	1	\N
6751	385	AMBIENTALES SPRAY GLADE EN SPRAY	COM5479	01	10	\N
6752	385	RECOGEDOR DE BASURA PLASTICO	COM5141	01	2	\N
6753	385	ESCOBA DE MADERA	COM5161	01	2	\N
6754	385	ESCOBA ZULY	COM5397	01	2	\N
6755	385	MICROFIBRAS	TTS0232	01	12	\N
6756	385	FRANELA ROJA	COM5583	01	10	\N
6757	385	ATOMIZADORES TORVI ATOMISADORES MEDIANOS	\N	\N	5	\N
6758	386	TE FRUTOS ROJOS	COM5505	01	2	\N
6759	386	VASOS TERMICOS 6 ONZ.	COM5468	01	3	\N
6760	386	VASOS PLASTICOS 7 ONZ.	COM5220	01	2	\N
6761	386	SERVILLETAS	ABS0112	01	2	\N
6762	386	CAFE BUEN DIA 170 GR	COM5247	01	1	\N
6763	386	AZUCAR DE 2 KG	COM5367	01	1	\N
6764	386	RESALTADOR ROSADO	OFI0065	07	1	\N
6765	386	REPUESTOS DE CUCHILLAS (ESTILETES)	OFI0125	07	1	\N
6766	386	TIJERAS	OFI0231	07	1	\N
6767	386	ESFERO AZUL	OFI0188	07	10	\N
6768	386	MARCADOR PERMANENTE PUNTA FINA NEGRO	OFI0268	07	6	\N
6769	386	RESMAS DE PAPEL BOND A4	OFI0031	07	4	\N
6770	386	PASTILLA BAÑO TANQUE	COM5339	01	2	\N
6771	386	ROLLO DE TOALLAS CAFÉ PARA MANOS 150 METROS	ABS0482	01	1	\N
6772	386	FUNDAS BASURA JUMBO NEGRAS 38*55 PAQ 10	COM5266	01	1	\N
6773	386	FILM STRECH PEQUEÑO	OFI0127	07	3	\N
6774	386	ESTILETES	OFI0069	07	3	\N
6775	386	JABON DESENGRASANTE DE MANOS (PARA MECANICA)	COM5577	01	1	\N
6776	386	DESINFECTANTE DE PISOS GALON	QUI1176	01	1	\N
6777	386	PEGAMENTO BONDER	COM5623	01	4	\N
6778	386	CINTA AISLANTE ELECTRICA	COM5401	01	4	\N
6779	386	MARCADORES PARA VIDRIO CAJA DE MARCADORES DE COLORES POR 10 UNIDADES\nPARA VIDRIO	OFI0323	07	12	\N
6780	386	JABON LIQUIDO GALON	QUI0572	01	1	\N
6781	386	PROTECTORES AUDITIVOS CON CORDON	COM5617	01	6	\N
6782	386	MICROFIBRAS	TTS0232	01	8	\N
6783	386	REPUESTOS DE MOPAS BLANCAS	COM5133	01	4	\N
6784	386	ESCOBA ZULY	COM5397	01	3	\N
6785	386	AMBIENTALES SPRAY GLADE EN SPRAY PRIMAVERA FRUTAL	COM5479	01	2	\N
6786	386	GUANTES PALMA AZUL G-40 TALLA 7	COM5621	01	10	\N
6787	386	FUNDAS BASURA BLANCAS PERFUMADAS	COM5256	01	3	\N
6788	386	FUNDA DINA 6 TIPO CAMISA	COM5103	01	4	\N
6789	386	DETERGENTE	COM5404	01	4	\N
6790	386	GUANTES NITRILO TALLA M	COM5488	01	3	\N
6791	387	RESMAS DE PAPEL BOND A4	OFI0031	07	10	\N
6792	387	RESALTADOR AMARILLO	OFI0063	07	3	\N
6793	387	ESFERO AZUL	OFI0188	07	10	\N
6794	387	LAPIZ	OFI0045	07	5	\N
6795	387	CORRECTOR	OFI0077	07	3	\N
6796	387	TIJERAS	OFI0231	07	3	\N
6797	387	CLIPS PEQUEÑOS	OFI0051	07	9	\N
6798	387	CLIPS MARIPOSA	OFI0172	07	4	\N
6799	387	SEPARADOR DE HOJAS	OFI0089	07	3	\N
6800	387	CINTA SCOTCH PEQUEÑA	OFI0040	07	8	\N
6801	387	CINTA DE EMBALAJE PEQUEÑA 200 MTRS	OFI0028	07	5	\N
6802	387	FILM STRECH MEDIANO	OFI0260	07	2	\N
6803	387	MARCADOR PARA PIZARRA AZUL	OFI0274	07	4	\N
6804	387	MARCADOR PARA PIZARRA NEGRO	OFI0275	07	4	\N
6805	387	CAJA DE VINCHAS PARA CARPETAS	OFI0242	07	2	\N
6806	387	SERVILLETAS	ABS0112	01	6	\N
6807	387	REMOVEDOR DE AZUCAR	COM5424	01	5	\N
6808	387	AZUCAR DE 2 KG	COM5367	01	4	\N
6809	387	CAFE DE PASAR MINERVA 1KG	COM5585	01	4	\N
6810	387	TE MANZANILLA	COM5320	01	1	\N
6811	387	TE MANZANILLA MIEL	COM5598	01	2	\N
6812	387	TE FRUTOS ROJOS	COM5505	01	2	\N
6813	387	CARPETA DE MANILA (PAQX10)	OFI0319	07	9	\N
6814	387	MARCADOR PERMANENTE PUNTA GRUESA NEGRO	OFI0155	07	3	\N
6815	387	FILM STRECH PEQUEÑO	OFI0127	07	4	\N
6816	387	FILM STRECH GRANDE	OFI0311	07	2	\N
6817	387	CLORO GALON	QUI5005	01	3	\N
6818	387	DESINFECTANTE DE PISOS GALON	QUI1176	01	4	\N
6819	387	FUNDAS BASURA INDUSTRIAL NEGRAS 30*36 PAQ 10	COM5253	01	5	\N
6820	387	FUNDAS BASURA JUMBO NEGRAS 38*55 PAQ 10	COM5266	01	10	\N
6821	387	PAPEL HIGIENICO JUMBO 500 METROS	ABS0373	01	10	\N
6822	387	PAPEL HIGIENICO PEQUEÑO	COM5592	01	1	\N
6823	387	ROLLO DE TOALLAS CAFÉ PARA MANOS 150 METROS	ABS0482	01	10	\N
6824	387	MICROFIBRAS PEQUEÑAS (PAQX3)	COM5507	01	5	\N
6825	387	LAVAVAJILLA CREMA 950 GR	COM5383	01	2	\N
6826	387	PROTECTOR DE HOJAS	OFI0252	07	9	\N
6827	387	CERA PARA PISOS CERAMICA	QUI0090	01	2	\N
6829	387	ESPATULA	COM5570	01	3	\N
6830	387	FUNDAS BASURA BLANCAS	COM5256	01	10	\N
6831	387	CERA PARA PISO FLOTANTE LIQUIDO PARA LIMPIAR PISO FLOTANTE	QUI0142	01	2	\N
6832	387	LUSTRE PARA PISOS # 8	COM0127	01	3	\N
6833	387	GUANTES NITRILO TALLA M	COM5488	01	2	\N
6834	387	GUANTES NITRILO TALLA L	COM5489	01	2	\N
6835	387	DESENGRASANTE PARA PISOS	QUI0123	01	4	\N
6836	387	JABON DE MANOS	QUI0572	01	2	\N
6837	387	ALCOHOL	QUI0080	01	3	\N
6838	387	DETERGENTE	COM5404	01	4	\N
6839	387	JABON LIQUIDO 500 ML	QUI0212	01	1	\N
6840	387	AMBIENTALES SPRAY GLADE EN SPRAY	COM5479	01	10	\N
6841	387	RECOGEDOR DE BASURA PLASTICO	COM5141	01	2	\N
6842	387	ESCOBA DE MADERA	COM5161	01	2	\N
6843	387	ESCOBA ZULY	COM5397	01	2	\N
6844	387	MICROFIBRAS	TTS0232	01	12	\N
6845	387	FRANELA ROJA	COM5583	01	10	\N
6846	387	ATOMIZADORES TORVI ATOMISADORES MEDIANOS	COM5620	01	5	\N
6847	388	RESMAS DE PAPEL BOND A4	OFI0031	07	10	\N
6848	388	RESALTADOR AMARILLO	OFI0063	07	3	\N
6849	388	ESFERO AZUL	OFI0188	07	10	\N
6850	388	LAPIZ	OFI0045	07	5	\N
6851	388	CORRECTOR	OFI0077	07	3	\N
6852	388	TIJERAS	OFI0231	07	3	\N
6853	388	CLIPS PEQUEÑOS	OFI0051	07	9	\N
6854	388	CLIPS MARIPOSA	OFI0172	07	4	\N
6855	388	SEPARADOR DE HOJAS	OFI0089	07	3	\N
6856	388	CINTA SCOTCH PEQUEÑA	OFI0040	07	8	\N
6857	388	CINTA DE EMBALAJE PEQUEÑA 200 MTRS	OFI0028	07	5	\N
6858	388	FILM STRECH MEDIANO	OFI0260	07	2	\N
6859	388	MARCADOR PARA PIZARRA AZUL	OFI0274	07	4	\N
6860	388	MARCADOR PARA PIZARRA NEGRO	OFI0275	07	4	\N
6861	388	CAJA DE VINCHAS PARA CARPETAS	OFI0242	07	2	\N
6862	388	SERVILLETAS	ABS0112	01	6	\N
6863	388	REMOVEDOR DE AZUCAR	COM5424	01	5	\N
6864	388	AZUCAR DE 2 KG	COM5367	01	4	\N
6865	388	CAFE DE PASAR MINERVA 1KG	COM5585	01	4	\N
6866	388	TE MANZANILLA	COM5320	01	1	\N
6867	388	TE MANZANILLA MIEL	COM5598	01	2	\N
6868	388	TE FRUTOS ROJOS	COM5505	01	2	\N
6869	388	CARPETA DE MANILA (PAQX10)	OFI0319	07	9	\N
6870	388	MARCADOR PERMANENTE PUNTA GRUESA NEGRO	OFI0155	07	3	\N
6871	388	FILM STRECH PEQUEÑO	OFI0127	07	4	\N
6872	388	FILM STRECH GRANDE	OFI0311	07	2	\N
6873	388	CLORO GALON	QUI5005	01	3	\N
6874	388	DESINFECTANTE DE PISOS GALON	QUI1176	01	4	\N
6875	388	FUNDAS BASURA INDUSTRIAL NEGRAS 30*36 PAQ 10	COM5253	01	5	\N
6876	388	FUNDAS BASURA JUMBO NEGRAS 38*55 PAQ 10	COM5266	01	10	\N
6877	388	PAPEL HIGIENICO JUMBO 500 METROS	ABS0373	01	10	\N
6878	388	PAPEL HIGIENICO PEQUEÑO	COM5592	01	1	\N
6879	388	ROLLO DE TOALLAS CAFÉ PARA MANOS 150 METROS	ABS0482	01	10	\N
6880	388	MICROFIBRAS PEQUEÑAS (PAQX3)	COM5507	01	5	\N
6881	388	LAVAVAJILLA CREMA 950 GR	COM5383	01	2	\N
6882	388	PROTECTOR DE HOJAS	OFI0252	07	9	\N
6883	388	CERA PARA PISOS CERAMICA	QUI0090	01	2	\N
6884	388	BROCHA #2	COM5606	01	2	\N
6885	388	ESPATULA	COM5570	01	3	\N
6886	388	FUNDAS BASURA BLANCAS	COM5256	01	10	\N
6887	388	CERA PARA PISO FLOTANTE LIQUIDO PARA LIMPIAR PISO FLOTANTE	QUI0142	01	2	\N
6888	388	LUSTRE PARA PISOS # 8	COM0127	01	3	\N
6889	388	GUANTES NITRILO TALLA M	COM5488	01	2	\N
6890	388	GUANTES NITRILO TALLA L	COM5489	01	2	\N
6891	388	DESENGRASANTE PARA PISOS	QUI0123	01	4	\N
6892	388	JABON DE MANOS	QUI0572	01	2	\N
6893	388	ALCOHOL	QUI0080	01	3	\N
6894	388	DETERGENTE	COM5404	01	4	\N
6895	388	JABON LIQUIDO 500 ML	QUI0212	01	1	\N
6896	388	AMBIENTALES SPRAY GLADE EN SPRAY	COM5479	01	10	\N
6897	388	RECOGEDOR DE BASURA PLASTICO	COM5141	01	2	\N
6898	388	ESCOBA DE MADERA	COM5161	01	2	\N
6899	388	ESCOBA ZULY	COM5397	01	2	\N
6900	388	MICROFIBRAS	TTS0232	01	12	\N
6901	388	FRANELA ROJA	COM5583	01	10	\N
6902	388	ATOMIZADORES TORVI ATOMISADORES MEDIANOS	COM5620	01	5	\N
6828	387	BROCHA #2	COM5320	01	2	\N
\.


--
-- TOC entry 5080 (class 0 OID 16390)
-- Dependencies: 220
-- Data for Name: pedidos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pedidos (id, numero_pedido, fecha, pdf_filename, email_uid, email_from, email_subject, sucursal, cliente_id, sucursal_id, estado, orden_compra) FROM stdin;
384	1000	2025-10-08 11:39:46.182048	\N	\N	\N	\N	GDR003 PATIO2 CUENCA	1	711	con_errores	OS-0-0-5338
385	1001	2025-10-08 11:45:25.224582	\N	\N	\N	\N	GRD031 PATIO TUMBACO	1	695	con_errores	OS-0-0-5452
386	1002	2025-10-08 12:10:21.328891	\N	\N	\N	\N	GDR003 PATIO2 CUENCA	1	711	procesado	OS-0-0-5338
388	1004	2025-10-08 12:31:11.089273	\N	\N	\N	\N	GRD031 PATIO TUMBACO	1	695	procesado	OS-0-0-5452
387	1003	2025-10-08 12:30:40.028437	\N	\N	\N	\N	GRD031 PATIO TUMBACO	1	695	por_procesar	OS-0-0-5452
\.


--
-- TOC entry 5105 (class 0 OID 106552)
-- Dependencies: 247
-- Data for Name: producto_alias; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.producto_alias (id, producto_id, cliente_id, alias, fecha_creacion, fecha_actualizacion) FROM stdin;
1388	2879	1	SERVILLETAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1389	2880	1	PAPEL HIGIENICO JUMBO 500 METROS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1390	2880	1	PAPEL HIGENICO JUMBO 400 METROS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1391	2881	1	ROLLO DE TOALLAS CAFÉ PARA MANOS 150 METROS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1392	2882	1	TOALLAS DE MANOS ELITE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1393	2882	1	TOALLAS DE MANOS SCOTT	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1394	2883	1	PAR DE GUANTES CAUCHO TALLA 7	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1395	2883	1	PAR DE GUANTES CAUCHO TALLA 7-1/2	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1396	2884	1	PAR DE GUANTES CAUCHO TALLA 8	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1397	2885	1	PAR DE GUANTES CAUCHO TALLA 8-1/2	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1398	2886	1	PAR DE GUANTES CAUCHO TALLA 9	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1399	2887	1	GUANTES PALMA AZUL G-40 TALLA 6	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1400	2887	1	GUANTES PALMA AZUL G-40 TALLA 7	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1401	2888	1	CUCHARAS PEQUEÑAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1402	2889	1	GUANTES PALMA AZUL G-40 TALLA 8	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1403	2889	1	GUANTES PALMA AZUL G-40 TALLA 9	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1404	2890	1	CEPILLO DE LAVADO CONTINUO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1405	2891	1	CEPILLO DE ROPA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1406	2891	1	CEPILLO PARA LAVAR BICICLETA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1407	2892	1	ESPONJA MIXTA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1408	2893	1	MICROFIBRAS PEQUEÑAS (PAQX3)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1409	2893	1	PAÑOS ABSORVENTE PAQ X 3 paños absorbentes	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1410	2894	1	CEPILLO PARA INODORO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1411	2894	1	CEPILLO PARA BAÑO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1412	2895	1	FUNDA DINA 6 TIPO CAMISA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1413	2896	1	TACHO DE BASURA PARA BAÑOS TACHO DE BASURA PARA BAÑOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1414	2897	1	MOPAS COMPLETAS BLANCA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1415	2898	1	MOPA BLANCA RECTANGULAR	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1416	2899	1	MOPAS COMPLETAS AZUL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1417	2900	1	REPUESTO MOPA MICROFIBRA 17X46	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1418	2901	1	RECOGEDOR DE BASURA PLASTICO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1419	2902	1	TIPS PASTILLAS AMBIENTAL DE BAÑO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1420	2903	1	ESCOBA DE MADERA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1421	2904	1	VASOS PLASTICOS 7 ONZ.	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1422	2905	1	CAFE BUEN DIA 170   GR	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1423	2906	1	ESCURRIDOR EXPLANDIBLE DE VIDRIOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1424	2906	1	ESCURRIDOR EXPLANDIBLE DE VIDRIOS ESCURRIDOR DE VIDRIOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1425	2907	1	FUNDAS BASURA INDUSTRIAL NEGRAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1426	2908	1	FUNDAS BASURA ESTANDAR NEGRAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1427	2909	1	FUNDAS BASURA BLANCAS PERFUMADAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1428	2910	1	FUNDAS BASURA JUMBO NEGRAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1429	2890	1	ESCOBILLON FULLER COMPLETO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1430	2911	1	FUNDA DINA 4  TIPO CAMISA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1431	2912	1	FUNDA DINA 1/2 TIPO CAMISA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1432	2913	1	PILA AAA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1433	2914	1	CAFE DE PASAR MINERVA 400 GRAMOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1434	2915	1	TE ANIS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1435	2915	1	TE CANELA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1436	2915	1	TE DE CEDRON	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1437	2915	1	TE DE HIERBA LUISA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1438	2915	1	TE HORCHATA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1439	2915	1	TE JAMAICA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1440	2915	1	TE MANZANILLA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1441	2916	1	TE MANZANILLA MIEL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1442	2917	1	INSECTICIDA SPRAY	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1443	2918	1	PASTILLA TANQUE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1444	2919	1	AZUCAR DE 2 KG	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1445	2920	1	REPUESTO DE ESCOBILLON FULLER	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1446	2921	1	LAVAVAJILLA CREMA 900 ML	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1447	2922	1	LAVAVAJILLA EN BARRA 500 GR	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1448	2923	1	REPUESTO AMBIENTAL GLADE ACEITE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1449	2924	1	REPUESTO PALO DE MADERA ESCOBA ZULY	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1450	2924	1	PALOS DE MADERA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1451	2925	1	ESCOBA ZULY	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1452	2926	1	REPUESTO CABEZAL ESCOBA ZULY	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1453	2926	1	REPUESTO DE ESCOBA ZULY CABEZAL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1454	2927	1	CINTA AISLANTE NEGRA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1455	2927	1	CINTA AISLANTE ELECTRICA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1456	2927	1	TAIPE NEGRO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1457	2928	1	DETERGENTE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1458	2929	1	RECOGEDOR DE BASURA METALICO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1459	2930	1	REMOVEDOR DE AZUCAR	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1460	2931	1	REPUESTO TUBO METALICO PARA ESCOBA ZULY	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1461	2932	1	VASOS TERMICOS 6 ONZ.	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1462	2933	1	BASURERO METALICO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1463	2934	1	AMBIENTALES SPRAY GLADE EN SPRAY	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1464	2935	1	ESPONJA VERDE VILEDA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1465	2936	1	GUANTES NITRILO TALLA M	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1466	2937	1	GUANTES NITRILO TALLA L	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1467	2938	1	TE FRUTOS ROJOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1468	2939	1	VASOS PLASTICOS 2 ONZ	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1469	2940	1	JABON DESENGRASANTE DE MANOS (PARA MECANICA)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1470	2941	1	LAVAVAJILLA LIQUIDO - 1 LITRO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1471	2942	1	FUNDA DINA 10 TIPO CAMISA RAYADA MEGA JUMBO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1472	2943	1	FUNDAS TRANSPARENTES 7*12 CM	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1473	2944	1	FRANELA ROJA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1474	2945	1	CAFE DE PASAR MINERVA 1KG	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1475	2946	1	JABON MACHO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1476	2947	1	AROMATIZANTE DE VEHICULO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1477	2948	1	GUANTES MICROFIBRA LA PARA LAVAR CARROS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1478	2949	1	FILTROS PARA CAFETERA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1479	2949	1	FILTROS PARA PASAR CAFÉ	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1480	2950	1	MATA MALEZA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1481	2951	1	BROCHA # 3	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1482	2952	1	BROCHA # 4	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1483	2953	1	BROCHA # 2	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1484	2954	1	PAPEL HIGIENICO BULL PACK	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1485	2955	1	PILAS RECARGABLES AAA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1486	2956	1	PILAS RECARGABLES AA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1487	2946	1	JABON AZUL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1488	2957	1	DESINFECTANTE LYSOL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1489	2958	1	AZUCAR DE 1 KG	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1490	2959	1	ATOMIZADORES TORVI	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1491	2960	1	BRUJITA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1492	2961	1	REPUESTO AMBIENTAL GLADE TOQUE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1493	2961	1	REPUESTO AMBIENTAL GLADE PULSO AUTOMATICO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1494	2962	1	CINTA DE EMBALAJE PEQUEÑA 200 MTRS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1495	2963	1	RESMAS DE PAPEL BOND A4	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1496	2964	1	CINTA SCOTCH PEQUEÑA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1497	2965	1	LAPIZ	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1498	2966	1	LEITZ NEGRA GRANDE LOMO FINO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1499	2967	1	BORRADOR BLANCO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1500	2968	1	BORRADOR DE PIZARRA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1501	2969	1	CLIPS PEQUEÑOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1502	2970	1	CARPETA LISTA DE PRECIOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1503	2971	1	CINTA MAGICA (PARA IMPRONTA)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1504	2972	1	RESALTADOR AMARILLO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1505	2973	1	RESALTADOR AZUL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1506	2973	1	RESALTADOR VERDE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1507	2974	1	RESALTADOR ROSADO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1508	2975	1	RESALTADOR TOMATE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1509	2975	1	RESALTADOR NARANJA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1510	2976	1	ESTILETES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1511	2977	1	SACA GRAPAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1512	2978	1	SACAPUNTAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1513	2979	1	CORRECTOR	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1514	2979	1	CORRECTOR TINTA CORRECTORA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1515	2980	1	CUADERNO CUADRICULADO PEQUEÑO 100 H	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1516	2981	1	CUADERNO CUADRICULADO UNIVERSITARIO 100 H	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1517	2982	1	SEPARADOR DE HOJAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1518	2983	1	ADHESIVO RECTANGULAR	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1519	2984	1	LEITZ NEGRA GRANDE LOMO GRUESO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1520	2985	1	MICA PARA PLASTIFICAR TAMAÑO A4	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1521	2986	1	REPUESTOS DE CUCHILLAS (ESTILETES)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1522	2987	1	FILM STRECH PEQUEÑO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1523	2984	1	LEITZ NEGRA GRANDE LOMO GRUESO  ARCHIVADOR OFICINA LOMO ANCHO AZUL A4	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1524	2988	1	MARCADOR PERMANENTE PUNTA GRUESA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1525	2988	1	MARCADOR PERMANENTE PUNTA GRUESA USO REPUESTOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1526	2989	1	ALMOHADILLA PARA DEDOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1527	2989	1	ALMOHADILLA PARA SELLOS SIN TINTA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1528	2990	1	TABLERO APOYAMANOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1529	2990	1	TABLERO APOYA MANOS PLASTICO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1530	2991	1	POST - IT	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1531	2991	1	POST IT	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1532	2991	1	BLOCK ADHESIVOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1533	2991	1	POST IT 5CM X 5CM (PAQ 500UNIDADES)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1534	2991	1	POST-IT 2*1.5 PULG	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1535	2992	1	CLIPS MARIPOSA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1536	2993	1	CAJA DE GRAPAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1537	2994	1	CINTA DOBLE FAZ	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1538	2995	1	CINTA ADHESIVA MASKING 1.2CM	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1539	2996	1	CERA PARA BILLETES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1540	2997	1	ESFERO AZUL 0.7	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1541	2997	1	ESFERO AZUL ESFERO AZUL 0.7	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1542	2998	1	ESFERO NEGRO 0.7	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1543	2999	1	ESFERO ROJO 0.7	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1544	3000	1	CUADROS ADHESIVOS DE COLORES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1545	3000	1	PAQUETE DE ETIQUETAS A COLORES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1546	3001	1	PAPEL CARBON AZUL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1547	3002	1	GOMA EN BARRA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1548	3003	1	PERFORADORA 50 HOJAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1549	3004	1	PORTACLIPS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1550	3005	1	REGLA METALICA 30 CM	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1551	3006	1	TIJERA GRANDE 21 CM	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1552	3007	1	TIJERAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1553	3008	1	TINTA PARA SELLOS AZUL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1554	3009	1	TINTA PARA SELLOS NEGRO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1555	3010	1	CAJA DE VINCHAS PARA CARPETAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1556	3011	1	FORMULARIO CONTINUO TROQUELADO (SIN COPIA)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1557	3012	1	FORMULARIO CONTINUO TROQUELADO (CON COPIA)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1558	3013	1	PROTECTOR DE HOJAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1559	3014	1	AMARRA PLASTICA 12CM	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1560	3015	1	FILM STRECH MEDIANO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1561	3016	1	SOBRE BOND TAMAÑO OFICIO (PAQX10)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1562	3017	1	SOBRE MANILA TAMAÑO F2	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1563	3017	1	SOBRE MANILA MEDIANOS (F2) (PAQX10)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1564	3018	1	SOBRE DE MANILA (F3 PAQUETE 10U)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1565	3018	1	SOBRE MANILA TAMAÑO A 4 (F3) (PAQX10)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1566	3019	1	SOBRE MANILA GRANDES (F6) (PAQX10)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1567	3020	1	SOBRES MANILA TAMAÑO A4 (F5)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1568	3021	1	MARCADOR PERMANENTE PUNTA FINA NEGRO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1569	3022	1	MARCADOR  PARA PIZARRA ROJO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1570	3023	1	MARCADOR  PARA PIZARRA AZUL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1571	3024	1	MARCADOR  PARA PIZARRA NEGRO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1572	3025	1	MARCADOR  PARA PIZARRA VERDE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1573	3026	1	MARCADOR PERMANENTE PUNTA FINA AZUL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1574	3027	1	MARCADOR PERMANENTE PUNTA FINA ROJO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1575	3028	1	BANDERITAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1576	3029	1	GRAPADORA 50 HOJAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1577	3030	1	BLOCK LETRA DE CAMBIO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1578	3030	1	BLOCK LETRAS DE CAMBIO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1579	3031	1	CALCULADORA CASIO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1580	3032	1	CARPETAS ACORDION A5	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1581	3033	1	FILM STRECH GRANDE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1582	3034	1	PAD MOUSE ERGONOMICO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1583	3034	1	PAD MOUSE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1584	3035	1	SOBRE MANILA PEQUEÑOS (F1) (PAQX10)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1585	3036	1	CARPETA  DE MANILA (PAQX10)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1586	3036	1	CARPETA DE MANILA (PAQX10) BEIGE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1587	3037	1	CINTA DE EMBALAJE  GRANDE 48X1000	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1588	3038	1	LAPIZ - CARYON DE CERA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1589	3039	1	MARCADOR PARA VIDRIO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1590	3040	1	MOUSE MOUSE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1591	3040	1	MOUSE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1592	3041	1	PERFORADORA INDUSTRIAL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1593	3042	1	AMARRA PLASTICA 30CM	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1594	3043	1	ALCOHOL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1595	3044	1	LIMPIA VIDRIO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1596	3045	1	CERA PARA PISOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1597	3045	1	CERA PARA PISOS CERAMICA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1598	3046	1	DESENGRASANTE DE MOTORES HD PLUS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1599	3047	1	DESENGRASANTE PARA PISOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1600	3048	1	CERA PARA PISO FLOTANTE P1	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1601	3049	1	DESINFECTANTE  DE PISOS LITRO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1602	3050	1	JABON LIQUIDO 500 ML	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1603	3051	1	ANTISARRO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1604	3051	1	ANTISARRO ANTISARRO EN SPRAY 600ML	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1605	3052	1	LUSTRA MUEBLES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1606	3053	1	JABON DE MANOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1607	3054	1	TOALLAS HUMEDAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1608	3055	1	DESINFECTANTE  DE PISOS GALON	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1609	3056	1	CLORO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1610	3057	1	REPUESTOS DE MOPAS AZULES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1611	3058	1	BASE MOPA BARRIDO 60 CM	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1612	3059	1	BASTON ALUMINIO PARA BASE Y SUJETADOR MOPA 140CM	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1613	3060	1	ESCURRIDOR DE PISOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1614	3061	1	MICROFIBRAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1615	3061	1	MICROFIBRAS PEQUEÑAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1616	3062	1	TAPONES AUDITIVOS LAVABLES CON CORDEL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1617	3063	1	PLUMERO DE MICROFIBRA CON MANGO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1618	3064	1	DISPENSADOR DE JABON LIQUIDO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1619	2909	1	FUNDAS BASURA BLANCAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1620	3018	1	SOBRES MANILA TAMAÑO A 4 (F3) (PAQX10)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1621	2949	1	PAQUETE DE FILTROS PARA CAFETERA 100 UNIDADES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1622	2909	1	FUNDAS BASURA BLANCAS fundas 18*23	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1623	2882	1	TOALLAS DE MANOS ELITE tres rollos de toallas de manos	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1624	2907	1	FUNDAS BASURA JUMBO NEGRAS funda 30*36	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1625	2918	1	PASTILLA TANQUE pastillas pato tanque	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1626	3065	1	MARCADOR PERMANENTE PUNTA GRUESA NEGRO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1627	3066	1	PAPEL HIGIENICO PEQUEÑO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1628	2921	1	LAVAVAJILLA CREMA 950 GR	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1629	2971	1	CINTA PARA IMPRONTA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1630	2894	1	ESCOBILLON DE INODORO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1631	2909	1	FUNDAS BASURA BLANCAS paquete de funda florar para baño	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1632	3067	1	PLATO PEQUEÑO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1633	3068	1	PLATO GRANDE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1634	2984	1	LEITZ NEGRA GRANDE LOMO GRUESO FOLDERS GRANDES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1635	3069	1	TRAPEADOR INDUSTRIAL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1636	2925	1	ESCOBA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1637	3070	1	PORTA ESFERO PORTALAPIZ	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1638	2991	1	POST IT BLOCKS DE NOTITAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1639	3036	1	CARPETA DE MANILA (PAQX10) 3 PAQUETES DE A 10	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1640	2880	1	PAPEL HIGIENICO JUMBO 500 METROS ROLLOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1641	2909	1	FUNDAS BASURA BLANCAS PAQUETES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1642	3048	1	CERA PARA PISO FLOTANTE 1 GALON	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1643	2922	1	LAVAVAJILLA EN CREMA 450GR	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1644	2937	1	GUANTES NITRILO TALLA L CAJA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1645	3071	1	DESINFECTANTE DE PISOS GALONES QUE NO SEA EUCALIPTO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1646	3053	1	JABON DE MANOS GALON	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1647	2910	1	FUNDAS BASURA JUMBO NEGRAS EXTRA GRANDES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1648	3061	1	MICROFIBRAS GRANDES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1649	2959	1	ATOMIZADORES 1 LITRO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1650	2890	1	CEPILLO DE LAVADO CONTINUO PARA LAVAR LOS AUTOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1651	3032	1	CARPETAS ACORDION A4	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1652	3046	1	DESENGRASANTE PARA VEHICULO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1653	3072	1	ALMORAL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1654	2900	1	REPUESTOS DE MOPAS BLANCAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1655	3020	1	SOBRE MANILA F5 (PAQX10)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1656	3073	1	SELLO ROJO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1657	3074	1	MARCADOR INDUSTRIAL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1658	3075	1	MARCADOR INDELEBLE ROJO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1659	3076	1	BALDE DE 16 LITROS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1660	2960	1	SUPER BONDER	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1661	2983	1	FUNDA ETIQUETAS HOJA 101*70MM NARANJA * 400 UNID	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1662	2921	1	LAVAVAJILLA CREMA 950 ML	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1663	2990	1	TABLERO APOYAMANOS PLASTICO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1664	3038	1	LAPIZ-CRAYON DE CERA ROJO ROJO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1665	2917	1	INSECTICIDA SPRAY PARA INSECTOS RASTREROS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1666	3077	1	PAPEL PARA SUMADORA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1667	3016	1	SOBRE TAMAÑO OFICIO (PAQX10)	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1668	3053	1	JABON LIQUIDO GALON	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1669	2887	1	PAR DE GUANTES DE CAUCHO TALLA 7	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1670	3056	1	CLORO GALON	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1671	3078	1	CLORO LITRO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1672	2908	1	FUNDAS BASURA ESTANDAR NEGRAS 23*28 PAQ 10	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1673	2910	1	FUNDAS BASURA JUMBO NEGRAS 38*55 PAQ 10	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1674	2918	1	PASTILLA BAÑO TANQUE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1675	3079	1	DISPENSADOR DE ROLLO DE PAPEL DE MANOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1676	3079	1	DISPENSADOR DE PAPEL TOALLA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1677	3080	1	TINTA PARA SELLOS ROJO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1678	2917	1	INSECTICIDA SPRAY ANIMALES RASTREROS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1679	2917	1	INSECTICIDA SPRAY ANIMALES VOLADORES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1680	2907	1	FUNDAS BASURA INDUSTRIAL NEGRAS 30*36 PAQ 10	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1681	3070	1	PORTA ESFERO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1682	2967	1	BORRADOR BLANCO BORRADOR	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1683	3081	1	PAPELERA PORTA PAPELES DE ESCRITORIO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1684	3082	1	RESMAS DE PAPEL BOND A5	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1685	3006	1	TIJERAS tecnicos taller	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1686	3060	1	ESCURRIDOR DE PISOS COMPLETO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1687	2991	1	POST IT 76MM	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1688	2925	1	ESCOBA ZULY cambia de escobas a los 6 meses	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1689	2928	1	DETERGENTE el mes anterior no nos despacharon	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1690	2879	1	SERVILLETAS X 100 SERVILLETAS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1691	2922	1	LAVAVAJILLA EN CREMA 450 GR	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1692	3083	1	JABON AZUL ALES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1693	3084	1	FUNDAS INDUSTRIALES COLOR VERDE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1694	2881	1	ROLLO DE TOALLAS CAFÉ PARA MANOS 300	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1695	2936	1	GUANTES NITRILO TALLA M GUANTES PARA EL SR. EDISON PACHACAMA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1696	2937	1	GUANTES NITRILO TALLA L GUANTES PARA EL SR. JOSE LUIS SALTOS	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1697	2889	1	PAR DE GUANTES CAUCHO TALLA 8 COLOR NEGRO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1698	3085	1	FUNDAS BASURA INDUSTRIAL CELESTES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1699	2925	1	ESCOBA ZULY ESCOBA SUAVE	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1700	3086	1	PIZZARA DE CORCHO 120X100 CON MARCO	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1701	3087	1	CAJA DE MANECILLAS 32MM NEGRO 12 UNI	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1702	3088	1	CINTA CARRETE PARA SUMADORA 13MM	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1703	3089	1	DESOXIDANTE DE METALES	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1704	3090	1	MOPA SIN COSTURA	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1705	3091	1	ESFERO AZUL	2025-10-24 00:55:24.983031	2025-10-24 00:55:24.983031
1718	2959	1	ATOMIZADORES TORVI ATOMISADORES MEDIANOS	2025-10-24 09:46:40.040001	2025-10-24 09:46:40.040001
\.


--
-- TOC entry 5089 (class 0 OID 24607)
-- Dependencies: 229
-- Data for Name: productos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.productos (id, sku, nombre, activo) FROM stdin;
2879	ABS0112	SERVILLETA BIOSOLUTIONS 24 CM X 24 CM  PAQUETE X 100  UND	t
2880	ABS0431	PH JUMBO BIOSOLUTION 500 MTS 1H X 1 U PACA X 12 U	t
2881	ABS0482	TOALLA INSTITUCIONAL NATURAL ECOLIMPIO 150 MT x 1 U PACA x  12	t
2882	ABS0494	TOALLA Z UNILIMPIO BLANCA 21X23CM X 150 UND X 12 UNIDADES	t
2883	COM5263	GUANTE MASTER C22 TALLA 7.5	t
2884	COM5277	GUANTE MASTER C22 TALLA 8	t
2885	COM5403	GUANTE MASTER C22 TALLA 8.5	t
2886	COM5366	GUANTE MASTER C22 TALLA 9	t
2887	COM5621	GUANTE DE TRABAJO NEGRO Y AZUL TALLA M	t
2888	COM5009	CUCHARITA BLANCA X 50UNID	t
2889	COM5622	GUANTE DE TRABAJO NEGRO Y ROJO TALLA L	t
2890	COM5274	CEPILLO PARA LAVAR AUTOS	t
2891	COM5081	CEPILLO ROPA PLANCHA VARIOS COLORES	t
2892	COM5083	ESPONJA SALVAUNAS MIXTA UNIDAD	t
2893	COM5090	PAÑO ESTRELLA HUMEDO ABSORBENTE X3	t
2894	COM5101	CEPILLO ESTRELLA SANITARIO CON BASE	t
2895	COM5103	FUNDA CAMISETA DINA 6 BLANCA PAQ X 100 UNDS	t
2896	COM5121	CONTENEDOR PEDAL 10 LTS NEGRO	t
2897	COM5128	SET DE MOPA MICROFIBRA PLANA 17X46	t
2898	COM5129	SET DE MOPA MICROFIBRA PLANA 15X92	t
2899	COM5659	SET MOPA BARRIDO 60CM AZUL	t
2900	COM5133	REPUESTO DE MOPA MICROFIBRA PLANA 17X46	t
2901	COM5141	RECOGEDOR DE BASURA VARIOS COLORES	t
2902	COM5616	PASTILLA AMBIENTAL TIPS 75 GR VARIOS AROMAS	t
2903	COM5161	ESCOBA DE COCO 30CM CON MANGO MADERA ECONOMICA	t
2904	COM5220	VASO 7 OZ TRANSPARENTE X 50 UNDS	t
2905	COM5247	CAFE BUEN DIA 170 GRS	t
2906	COM5250	LIMPIAVIDRIOS EXTENDIBLE CON PALO DE ALUMINIO	t
2907	COM5253	FUNDA PARA DESECHOS 30X36X1.1 NEGRA PAQ X 10 UND	t
2908	COM5254	FUNDA PARA DESECHOS 23X28X1 NEGRA PAQ X 10UND	t
2909	COM5256	FUNDA PARA DESECHOS 18X20X1 BLANCA PAQ X 10UND	t
2910	COM5266	FUNDA PARA DESECHOS 38X55X1.5 NEGRA PAQ X 10 UNDS	t
2911	COM5286	FUNDA CAMISETA DINA 4 BLANCA PAQ X 90 UNDS	t
2912	COM5301	FUNDA DINA 1/2 BLANCA	t
2913	com5306	PILA ENERGIZER AAA	t
2914	COM5317	CAFE MINERVA CLASICO X400GRS	t
2915	COM5320	TE ILE VARIOS AROMAS	t
2916	COM5598	TE MANZANILLA CON MIEL	t
2917	COM5336	PAFF INSECTICIDA MULTI 360cc	t
2918	COM5339	TIPS TANQUE BRISA MARINA	t
2919	COM5367	AZUCAR LA TRONCAL 2KG	t
2920	COM5381	REPUESTO ESCOBA LAVA CARROS	t
2921	COM5383	LAVAVAJILLAS TIPS 950 GR VARIOS AROMAS	t
2922	COM5384	LAVAVAJILLAS TIPS 450 GR VARIOS AROMAS	t
2923	COM5396	AIRWICK LIRIOS DE LUNA PAQ X 2 UNDS	t
2924	COM5397	TUBO ESCOBA ECONOMICA M/MADERA	t
2925	COM5648	ESCOBA EC CERDA SUAVE + MANGO DE MADERA	t
2926	COM5398	REPUESTO ESCOBA ECONOMICA M/MADERA	t
2927	COM5401	CINTA AISLANTE NEGRA	t
2928	COM5404	DETERGENTE 1 KILO BLANCO ULTREX	t
2929	COM5407	RECOGEDOR BASURA METALICO	t
2930	COM5424	SORBETE CAFETERO PAQ X 150 UNDS	t
2931	COM5465	TUBO ESCOBA METALICO ESTRELLA	t
2932	COM5468	VASO 6 oz TERMICO PAQ  X  20 UNID	t
2933	COM5474	PAPELERA REJILLA GRANDE	t
2934	COM5479	AMBIENTAL TIPS AEROSOL VARIOS AROMAS 360ML	t
2935	COM5487	FIBRA SUAVE VERDE MASTER	t
2936	COM5488	GUANTE DE NITRILO NEGRO 5.5 TALLA M	t
2937	COM5489	GUANTE DE NITRILO NEGRO 5.5 TALLA L	t
2938	COM5597	TE FRUTOS ROJOS	t
2939	COM5513	VASOS SALSEROS 2 OZ CON TAPA PAQ X 100 UNDS	t
2940	COM5577	DESENGRASANTE EN CREMA PARA MANOS GL	t
2941	COM5578	LAVAVAJILLAS TIPS LIQUIDO 650 ML VARIOS AROMAS	t
2942	COM5581	FUNDA DINA 10 NEGRA PAQ X 90 UNDS	t
2943	COM5582	FUNDA TRANSPARENTE 7X11	t
2944	COM5583	FRANELA ROJA ECONOMICA X 1 UND	t
2945	COM5585	CAFE DE PASAR MINERVA 1 KG X 1 UND	t
2946	COM5586	JABON MACHO AZUL 480 GR X 1 UND	t
2947	COM5587	AROMATIZANTE DE VEHICULO GALON VARIOS AROMAS X 1 UND	t
2948	COM5590	GUANTE MICROFIBRA PARA LAVADO DE AUTO	t
2949	COM5602	FILTRO PARA CAFE 8 CM PAQX100 UNDS	t
2950	COM5603	MATA MONTES 1KG	t
2951	COM5604	BROCHA CON MANGO DE MADERA "3	t
2952	COM5605	BROCHA CON MANGO DE MADERA "4	t
2953	COM5606	BROCHA CON MANGO DE MADERA "2	t
2954	COM5609	PAPEL HIGIENICO BULLPACK K X 250 HOJAS 1 UND	t
2955	COM5610	PILA ENERGIZER RECARGABLE AAA PAQ X 2 UNDS	t
2956	COM5611	PILA ENERGIZER RECARGABLE AA PAQ X 2 UNDS	t
2957	COM5613	DESINFECTANTE LYSOL 19 OZ	t
2958	COM5619	AZUCAR DE 1 KG	t
2959	COM5620	ATOMIZADOR TORVI 750ML	t
2960	COM5623	PEGAMENTO SUPER BONDER	t
2961	DIS0109	RECARGA DISPENSADOR DIGITAL HARMONY 3400 APLICACIONES	t
2962	OFI0028	CINTA DE EMPAQUE TRANS 200X48	t
2963	OFI0031	RESMA PAPEL BOND 75G A4  500U	t
2964	OFI0040	CINTA SCOTH T30 36x18	t
2965	OFI0045	LAPIZ  2HB	t
2966	OFI0046	FOLDER 2 ARG NEGRO	t
2967	OFI0048	BORRADOR PZ20	t
2968	OFI0049	BORRADOR DE PIZARRA UNIVERSITARIA	t
2969	OFI0051	CAJA CLIPS	t
2970	OFI0055	LISTADO 40 HOJAS	t
2971	OFI0056	CINTA MAGICA	t
2972	OFI0063	RESALTADOR AMARILLO	t
2973	OFI0064	RESALTADOR VERDE	t
2974	OFI0065	RESALTADOR ROSADO	t
2975	OFI0066	RESALTADOR TOMATE	t
2976	OFI0069	CUCHILLA GRANDE 18MM	t
2977	OFI0075	SACAGRAPAS PLAST	t
2978	OFI0076	SACAPUNTAS METAL	t
2979	OFI0077	CORRECTOR	t
2980	OFI0078	ESPIRAL 100H CUADERNOS	t
2981	OFI0086	UNIV 100H ESCRIBE ANDINO CUADROS (7861084213)	t
2982	OFI0089	SEPARADOR PLAST. OFFISOT 10 HOJAS	t
2983	OFI0100	FUNDA ETIQUETA T22 LARGAS VARIIOS COLORES ABRO	t
2984	OFI0139	ARCHIVADOR ESTUDIO 7CM  CAMBIO DE DESCRIPCION	t
2985	OFI0114	MICA PANDI A4	t
2986	OFI0336	REPUESTO CUCHILLA GRA. POINTER   C/UNO  x 10	t
2987	OFI0127	ROLLO PLASTICO STRECH FILM 12.5CM 1 KG	t
2988	OFI0155	MARCADOR ZEYAR PERMAN NEGRO ZP 1744	t
2989	OFI0158	ALMOHADILLA HUHUA 182 #2 SIN TINTA	t
2990	OFI0160	APOYAMANOS OFFISOT  CB 2302 A4 C/SOLIDOS  PLASTICO	t
2991	OFI0167	BLOCK ADHE 3X3	t
2992	OFI0172	CAJA CLIPS IMPRESS MARIPOSA 50 UNID	t
2993	OFI0174	CAJA GRAPAS EAGLE 1005NX 26/6 (5000) GRANDE	t
2994	OFI0177	CINTA DOBLE FAZ  DITECH D1510 1.5CNTX10M	t
2995	OFI0179	CINTA MASKING FANTAPE  40X18 ESCOLAR VERDE	t
2996	OFI0181	CREMA PELIKAN D2 PARA CONTAR C/U 14 GR	t
2997	OFI0188	ESFERO ESTILO 0.7MM  AZUL	t
2998	OFI0189	ESFERO ESTILO 0.7MM  NEGRO	t
2999	OFI0190	ESFERO ESTILO 0.7MM  ROJO	t
3000	OFI0200	FUNDA ETIQ. HOJA  101*70MM VERDE	t
3001	OFI0210	HOJA PAP. CARBON SHUN SHIP AZUL Y NEGRO	t
3002	OFI0219	PEGA BESTER EN BARRA 21 GRS	t
3003	OFI0221	PERFORADORA EAGLE 837  25H	t
3004	OFI0224	PORTA CLIPS PANDI CUADRADO  3044 NEGRO	t
3005	OFI0228	REGLA METALICA  30 CM. OFFISOT H8612-30	t
3006	OFI0230	TIJERA DL85  8.6" 21CM	t
3007	OFI0231	TIJERA ESCOLAR OFFISOT GK-3205-1 COL  MS-001	t
3008	OFI0237	TINTA ALMOHADILLA LANCER AZUL 24ML	t
3009	OFI0238	TINTA ALMOHADILLA LANCER NEGRA 24ML	t
3010	OFI0242	VINCHA METALICA OFFISOT C/CAJA X50	t
3011	OFI0247	PAPEL TROQUELADO 2000H	t
3012	OFI0314	PAPEL TROQUELADO 1 COPIA A LA MITAD 680 H	t
3013	OFI0252	PROTECTOR DE HOJA A4 FINO (paq 10)	t
3014	OFI0253	AMARRAS 12 CM TRANS. PAQ 100U	t
3015	OFI0260	STRETCH DE 18 MIC X 38 CM 200 MTS	t
3016	OFI0261	SOBRE IDEAL OF. BLANCO 60G. 24*11.5 PAQ X 10 UNDS	t
3017	OFI0262	SOBRE MANILA F2 19*26 CM PAQ X 10 UNDS	t
3018	OFI0263	SOBRE MANILA F3 23*32.4 CM PAQ X 10 UNDS	t
3019	OFI0265	SOBRE MANILA F6 30*40 CM PAQ X 10 UNDS	t
3020	OFI0266	SOBRE MANILA F5 27.5*37 CM PAQ X 10 UNDS	t
3021	OFI0268	MARCADOR FABER F/CD P/F NEGRO ACETATO 0.8MM	t
3022	OFI0273	MARCADOR PARA PIZARRA ECONOMICO ROJO	t
3023	OFI0274	MARCADOR PARA PIZARRA ECONOMICO AZUL	t
3024	OFI0275	MARCADOR PARA PIZARRA ECONOMICO NEGRO	t
3025	OFI0276	MARCADOR PARA PIZARRA ECONOMICO VERDE	t
3026	OFI0277	MARCADOR PARA CD PF ECONOMICO AZUL	t
3027	OFI0278	MARCADOR PARA CD PF ECONOMICO ROJO	t
3028	OFI0284	BANDERITAS OFFISOT X 5 UNDS	t
3029	OFI0286	ENGRAPADORA 900MB METAL	t
3030	OFI0306	BLOCK DE LETRA DE CAMBIO	t
3031	OFI0307	CALCULADORA JOINUS JS-956	t
3032	OFI0308	CARPETA ACORDEON PEQ CHEQUES	t
3033	OFI0311	ROLLO STRETCH FILM 50 CM 3 KILOS	t
3034	OFI0313	PAD MOUSE GEL	t
3035	OFI0318	SOBRE F1 MANILLA PAQ X 10 UND	t
3036	OFI0319	FOLDER MANILA 150 GR SIN VINCHA X 10	t
3037	OFI0320	CINTA DE EMPAQUE TRANS 48X1000	t
3038	OFI0322	LAPIZ CRAYON DE CERA NEGRO CAJA 12 UNID	t
3039	OFI0323	MARCADOR PARA VIDRIO 1 UND	t
3040	OFI0324	MOUSE XTM-205 CON CABLE	t
3041	OFI0328	PERFORADORA TRIO ALTO PODER 100 HOJAS	t
3042	OFI0329	AMARRA P/CABLE FHS-4X300 1.2MM BLANCO 100 PCS	t
3043	QUI0080	ALCOHOL MULTIPROPOSITOS 3785 ML (GL)	t
3044	QUI0085	LIMPIAVIDRIOS OZZ 3785 ML (GL)	t
3045	QUI0090	CERA AUTOBRILLANTE OZZ GALON	t
3046	QUI0092	DESENGRASANTE TORNADO OZZ GALON CAJA X 6 UNIDADES	t
3047	QUI0123	DESENGRASANTE ECOLIMPIO GALON CAJA X 6 UNIDADES	t
3048	COM5660	LIMPIADOR DE PISO FLOTANTE X 4 LITROS	t
3049	QUI0147	DESINFECTANTE OZZ AROMATERAPIA LAVANDA LITRO CAJA X 12 UNIDADES	t
3050	QUI0212	JABON LIQUIDO ANTIBACTERIAL DR CLEAN FLORAL 500 ML	t
3051	QUI0222	ANTISARRO OZZ CON ATOMIZADOR 600 ML	t
3052	QUI0288	BRILLA MUEBLES OZZ SPRAY 250 ML	t
3053	QUI0572	JABON ECOLIMPIO ALMENDRA GALON X 6 UND	t
3054	QUI0912	TOALLAS HUMEDAS DESINFECTANTES Y DESENGRASANTES UNILIMPIO PAQUETE X 45 U	t
3055	QUI1176	DESINFECTANTE FANTASIA MARINA ECO-INST 3 785 ML	t
3056	QUI5005	CLORO ECONOMICO GALON	t
3057	TTS0002	MOPA POLVO ACRILICA BOLSILLO 60 CM	t
3058	TTS0037	BASE MOPA BARRIDO 60 CM	t
3059	TTS0048	BASTON ALUMINIO PARA BASE Y SUJETADOR MOPA 140CM	t
3060	COM5638	ESCURRIDOR PISOS MANNGO DE ALUMINIO 75CM	t
3061	TTS0232	PAÑO MICROFIBRA CELESTE 39X40 CM	t
3062	COM5617	TAPONES AUDITIVOS LAVABLES CON CORDEL	t
3063	COM5629	PLUMERO DE MICROFIBRA CON MANGO	t
3064	DIS0550	DISPENSADOR MULTI-VALVULA TRANSLUCIDO UNILIMPIO CAJA X 10	t
3065	OFI0303	MARCADOR PERMANENTE NEGRO 1 UND	t
3066	ABS0452	PAPEL HIGIENICO SUAVE GOLD 32M 3 HOJAS BULTO*4	t
3067	COM5107	PLATO PEQUEÑO X 25 UNDS	t
3068	COM5231	PLATO #8 COLOR BLANCO PAQ POR 25 UNDS	t
3069	COM5313	TRAPEADOR INDUSTRIAL 40CM	t
3070	OFI0120	PORTALAPIZ MET. CUADRADA MALLA NEGRA 8*9.7CM	t
3071	QUI1178	DESINFECTANTE ECOLIMPIO LAVANDA GALON X 6 UND	t
3072	QUI0130	SILICONE HI-WAY GALON  CAJA X 6	t
3073	COM5527	LEJIA SELLO ROJO ESCAMAS 375 GR	t
3074	OFI0333	MARCADOR INDUSTRIAL EDING 500 AZUL	t
3075	OFI0327	MARCADOR INDELEBLE	t
3076	COM5503	BALDE VARIOS COLORES 16 LITROS	t
3077	OFI0316	ROLLO SUMADORA BOND 57*30 METROS	t
3078	QUI0173	CLORO LIQUIDO OZZ 5.5%  LITRO	t
3079	DIS0436	DISPENSADOR AUTOCUT NEGRO SJ T7400TBK  a comodato	t
3080	OFI0108	TINTA ALMOHADILLA LANCER ROJO 24 ML	t
3081	OFI0115	PAPELERA METALICA 3 PISOS NEGRA	t
3082	OFI0032	RESMA PAPEL BOND 75G A5  500U	t
3083	COM5108	JABON AZUL MAQUIMADO ALES 240 GR	t
3084	COM5392	FUNDA PARA DESECHOS 30X36 VERDE 1.2	t
3085	COM5259	FUNDA PARA DESECHOS 30X36X1.2 CELESTE PAQ X 10UND	t
3086	OFI0332	PIZZARA DE CORCHO 120X100 CON MARCO	t
3087	OFI0334	CAJA DE MANECILLAS 32MM NEGRO 12 UNI	t
3088	OFI0335	CINTA CARRETE PARA SUMADORA 13MM	t
3089	COM5644	DESOXIDANTE FOSFATIZANTE PARA METALES DE 1 LITRO	t
3090	COM5645	TRAPEADOR REDONDO 500GR	t
3091	OFI0185	ESFERO BIC ROUNDER AZUL	t
3110	TEST001	TEST	t
3111	TEST	TESTESTEST	t
\.


--
-- TOC entry 5087 (class 0 OID 24590)
-- Dependencies: 227
-- Data for Name: sucursales; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sucursales (id, cliente_id, alias, nombre, encargado, direccion, activo, almacen, ruc, ciudad) FROM stdin;
714	1	PATIO QUITO NORTE	GDR001 PATIO QUITO NORTE	Jorge Guatemal	AV. GALO PLAZA Y FRANCISCO DALMAU	t	GDR001 PAT	0190391906001	QUITO NORTE
711	1	PATIO 2 CUENCA	GDR003 PATIO2 CUENCA	Jennifer Arpi	Av España y Segovia frente a SECOHI	t	GDR003 PAT	0190391906001	CUENCA
687	1	QUITO - SANGOLQUI	GDR004 PATIO QUITO SANGOLQUI	Patricia Tipan	(AVDA. LOS SHIRYS N100 Y ALTAR	t	GDR004 PAT	0190157075001	QUITO - SANGOLQUI
702	1	PATIO SAMBORONDON EL PAN SHOWROOM	GDR016 PATIO SAMBORONDON	Enrique Hidalgo	AV. MIGUEL YUNEZ SN Y KM. 14.5	t	GDR016 PAT	0190316025001	SAMBORONDON - EL PAN
689	1	PATIO GUAYAQUIL LAS AMERICAS	GDR018 PATIO GUAYAQUIL LAS AMERICAS	Alisson Barberan Murillo	AV. DE LAS AMERICAS Y EL TERMINAL 2	t	GDR018 PAT	0190391906001	GUAYAQUIL
696	1	MATRIZ CUENCA	GRD002 MATRIZ CUENCA	Cristian Arce	Av España 8-99 y Sevilla	t	GRD002 MAT	0190157075001	CUENCA
691	1	CUENCA MATRIZ	GRD002 MATRIZ CUENCA	Andrea Naranjo	Av España 8-99 y Sevilla	t	GRD002 MAT	0190316025001	CUENCA
698	1	CUENCA MATRIZ	GRD002 MATRIZ CUENCA	Cristina Campos	(AVDA. ESPAÑA 899 Y SEVILLA)	t	GRD002 MAT	0190316025001	CUENCA
697	1	CUENCA MATRIZ	GRD002 MATRIZ CUENCA	Cristina Campos	(AVDA. ESPAÑA 899 Y SEVILLA)	t	GRD002 MAT	0190157075001	CUENCA
708	1	PATIO QUITO SANGOLQUI	GRD004 PATIO QUITO SANGOLQUI	Isabel Posligua	(AV LOS SHIRYS Y VIA AMAGUANA LOTE NRO 2	t	GRD004 PAT	0190316025001	QUITO - SANGOLQUI
690	1	PATIO IBARRA	GRD005 PATIO IBARRA	Andrea García Moreira	VIA A IBARRA Y ATUNTAQUI	t	GRD005 PAT	0190401030001	IBARRA
705	1	PATIO QUITO 6 DE DICIEMBRE	GRD006 PATIO QUITO 6 DE DICIEMBRE	Genesis  Zambrano	(AV 6 DE DICIEMBRE Y GALO PLAZA LAZO	t	GRD006 PAT	0190401030001	QUITO
716	1	PATIO MANTA	GRD011 PATIO MANTA	Joselyn Barrezueta	(AV 4 DE NOVIEMBRE Y CALLE 321	t	GRD011 PAT	0190157075001	MANTA
737	1	PATIO QUITO NORTE	GDR001 PATIO QUITO NORTE	Tatiana Aguirre	AV. GALO PLAZA Y FRANCISCO DALMAU	t	GDR001 PAT	0190316025001	QUITO NORTE
735	1	PATIO QUITO NORTE	GDR001 PATIO QUITO NORTE	Segundo Alvaro	AV. GALO PLAZA Y FRANCISCO DALMAU	t	GDR001 PAT	0190391906001	QUITO NORTE
729	1	PATIO 2 CUENCA	GDR003 PATIO2 CUENCA	Mayra Amay	AVDA. ESPANA Y SEGOVIA FRENTE A SECOHI	t	GDR003 PAT	0190316025001	CUENCA
731	1	PATIO QUITO SANGOLQUI	GDR004 PATIO QUITO SANGOLQUI	Raquel Solorzano	(AV LOS SHIRYS Y VIA AMAGUANA LOTE NRO 2	t	GDR004 PAT	0190391906001	QUITO - SANGOLQUI
730	1	PATIO QUITO 6 DE DICIEMBRE	GDR006 PATIO QUITO 6 DE DICIEMBRE	Mayra Peralvo	(AV 6 DE DICIEMBRE Y GALO PLAZA LAZO	t	GDR006 PAT	0190391906001	QUITO - 6 DICIEMBRE
724	1	PATIO GUAYAQUIL VIA DAULE	GDR010 PATIO GUAYAQUIL VIA DAULE	Lizzie Bravo	VIA DAULE KM 4 1/2 Y AV. MARTHA DE ROLDOS	t	GDR010 PAT	0190413993001	VIA DAULE
725	1	PATIO GUAYAQUIL VIA DAULE	GDR010 PATIO GUAYAQUIL VIA DAULE	Luis Castro	Kilómetro 4  1/2 VIA DAULE	t	GDR010 PAT	0190391906001	VIA DAULE
734	1	PATIO GUAYAQUIL LAS AMERICAS	GDR018 PATIO GUAYAQUIL LAS AMERICAS	Sandra Lavayen	AV LAS AMERICAS Y EL TERMINAL 2	t	GDR018 PAT	0190401030001	GUAYAQUIL
727	1	PATIO CUENCA DON BOSCO	GDR020 PATIO CUENCA DON BOSCO	Margarita Fajardo	ALONSO QUIJANO Y YANUNCAY)	t	GDR020 PAT	0190391906001	CUENCA
720	1	CUENCA MATRIZ	GRD002 MATRIZ CUENCA	Karina Andrade	Av España 8-99 y Sevilla	t	GRD002 MAT	0190157075001	CUENCA
726	1	PATIO QUITO CARAPUNGO	GRD008 PATIO QUITO CARAPUNGO	Ma. Belén Burbano	(AV. SIMON BOLIVAR Y N69H	t	GRD008 PAT	0190316025001	QUITO - CARAPUNGO
721	1	PATIO MANTA	GRD011 PATIO MANTA	Katherine Vera	AV 4 DE NOVIEMBRE  FRENTE A MAQUIDRAZ	t	GRD011 PAT	0190316025001	MANTA
728	1	PATIO MANTA	GRD011 PATIO MANTA	María José Perero	AV 4 DE NOVIEMBRE  FRENTE A MAQUIDRAZ	t	GRD011 PAT	0190391906001	MANTA
719	1	PATIO GUAYAQUIL JTM	GRD012 PATIO GUAYAQUIL JTM	Karen Ronquillo	AV. JUAN TANCA MARENGO SN Y TARQU	t	GRD012 PAT	0190413993001	GUAYAQUIL
700	1	PATIO GUAYAQUIL JTM	GRD012 PATIO GUAYAQUIL JTM	Diana Guillen	AV JUAN TANCA MARENGO	t	GRD012 PAT	0190391906001	GUAYAQUIL
694	1	PATIO GUAYAQUIL JTM	GRD012 PATIO GUAYAQUIL JTM	Betty Sanchez	AV JUAN TANCA MARENGO	t	GRD012 PAT	0190401030001	GUAYAQUIL
713	1	PATIO GUAYAQUIL JTM	GRD012 PATIO GUAYAQUIL JTM	Johanna Moran	AV JUAN TANCA MARENGO	t	GRD012 PAT	0190316025001	GUAYAQUIL
717	1	PATIO GUAYAQUIL JTM	GRD012 PATIO GUAYAQUIL JTM	Juliana Bustamante	AV JUAN TANCA MARENGO	t	GRD012 PAT	0190391906001	GUAYAQUIL
715	1	PATIO CUENCA YANUNCAY CONTROL SUR	GRD013 PATIO CUENCA YANUNCAY CONTROL SUR	Jorge Vivar	JUAN LARREA GUERRERO Y EC	t	GRD013 PAT	0190391906001	CUENCA
706	1	PATIO CUENCA YANUNCAY CONTROL SUR	GRD013 PATIO CUENCA YANUNCAY CONTROL SUR	Gianella Jara	JUAN LARREA GUERRERO	t	GRD013 PAT	0190168905001	CUENCA
738	1	PATIO LOJA	GRD014 PATIO LOJA	Viviana Montaño	AV. ISIDRO AYORA Y AV. VELASCO IBARRA	t	GRD014 PAT	0190316025001	LOJA
732	1	PATIO CUENCA TERMINAL TERRESTRE	GRD015 PATIO CUENCA TERMINAL TERRESTRE	Rocio Gonzalez	AV. ESPAÑA Y SEBASTIAN	t	GRD015 PAT	0190391906001	CUENCA
701	1	PATIO SAMBORONDON EL PAN SHOWROOM	GRD016 PATIO SAMBORONDON	Emily Gaibor	AV. MIGUEL YUNEZ SN Y KM. 14.5	t	GRD016 PAT	0190391906001	SAMBORONDON - EL PAN
692	1	PATIO CUENCA LAZARETO	GRD017 PATIO CUENCA LAZARETO	Andres Bacuilima	VIA SININCAY S/N	t	GRD017 PAT	0190457354001	CUENCA
688	1	PATIO MACHALA JETOUR	GRD019 PATIO MACHALA JETOUR	Jessi Arias	AV. 25 DE JUNIO S/N Y ALEJANDRO CASTRO B	t	GRD019 PAT	0190401030001	MACHALA
718	1	PATIO CC AVALON	GRD021 PATIO CC AVALON ¨SAMBORONDON¨	Jully Bonilla	CC AVALON PLAZA 3 LA AURORA SATELITE	t	GRD021 PAT	0190457354001	GUAYAQUIL
712	1	PATIO MACHALA	GRD023 PATIO MACHALA	Jessica Fierro	AV. 25 DE JUNIO S/N Y VIA A PASAJE)	t	GRD023 PAT	0190413993001	MACHALA
723	1	PATIO MACHALA	GRD023 PATIO MACHALA JACK	Laura Morales	AV. 25 DE JUNIO S/N Y VIA A PASAJE)	t	GRD023 PAT	0190316025001	MACHALA
704	1	CUENCA MATRIZ	GRD027 CM MATRIZ	Gabriel Parra	Av España 9-10	t	GRD027 CM 	0190428338001	CUENCA
736	1	PATIO YANTZAZA	GRD028 YANTZASA-PUYO	Silvia  Sanchez	AV. CUXIBAMBA Y TULCAN ESQUINA	t	GRD028 YAN	0190413993001	YANTZAZA
733	1	PATIO 12 DE OCTUBRE	GRD030 PATIO 12 DE OCTUBRE	Rosalía Prieto	12 DE OCTUBRE Y CRISTOBAL COLON	t	GRD030 PAT	0190457354001	CUENCA
707	1	PATIO 12 DE OCTUBRE	GRD030 PATIO 12 DE OCTUBRE	Isabel Alvarracin	12 DE OCTUBRE Y CRISTOBAL COLON	t	GRD030 PAT	0190391906001	CUENCA
693	1	PATIO 12 DE OCTUBRE	GRD030 PATIO 12 DE OCTUBRE	Anthony Pacheco	12 DE OCTUBRE Y CRISTOBAL COLON	t	GRD030 PAT	0190391906001	CUENCA
699	1	PATIO  QUITO TUMBACO	GRD031 PATIO TUMBACO	Cristopher Mencias	INTEROCEANICA S/N Y NORBERTO SALAZAR	t	GRD031 PAT	0190391906001	QUITO-TUMBACO
695	1	PATIO QUITO TUMBACO	GRD031 PATIO TUMBACO	Carla Romero	AV. INTEROCEANICA S/N Y NORBETO SALAZAR	t	GRD031 PAT	0190316025001	QUITO-TUMBACO
709	1	PATIO RIOBAMBA	GRD038 PATIO RIOBAMBA	Ivón Zuñiga	PANAMERICANA NORTE ESQ BOLIVAR SN LIZARZABURU	t	GRD038 PAT	0190316025001	RIOBAMBA
722	1	PATIO RIOBAMBA	GRD038 PATIO RIOBAMBA	Kevin Ricardo Garcia	PANAMERICANA NORTE ESQ BOLIVAR SN LIZARZABURU	t	GRD038 PAT	0190391906001	RIOBAMBA
710	1	PATIO RIOBAMBA	GRD038 PATIO RIOBAMBA	Ivón Zuñiga	PANAMERICANA NORTE ESQ BOLIVAR SN LIZARZABURU	t	GRD038 PAT	0190391906001	RIOBAMBA
703	1	PATIO PDI MANTA	GRD039 PATIO PDI MANTA	Erika Lopez	(VIA CIRCUNVALACION TRAMO 3 Y TRAMO Y	t	GRD039 PAT	0190382796001	MANTA
\.


--
-- TOC entry 5101 (class 0 OID 81985)
-- Dependencies: 243
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios (id, username, password_hash, nombre_completo, email, activo, fecha_creacion, ultimo_acceso) FROM stdin;
1	admin	$2b$12$JFj16UlGErHjsvwEDMVkbum2Z7RlGdC9nMIxEJFTvPhGq4Nx7.CqO	Administrador	admin@unilimpiosur.com	t	2025-10-06 05:28:45.609846	2025-10-24 00:54:30.882556
2	tyrone	$2b$12$jEGK5AenCC8bDcwe5E2O.Oq/Ck15/5RfmgvMMWW2MpELuFKZSg8SS	Tyrone	tyrone@unilimpiosur.com	t	2025-10-06 05:40:52.304777	2025-10-24 09:40:01.58967
\.


--
-- TOC entry 5132 (class 0 OID 0)
-- Dependencies: 236
-- Name: alias_productos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.alias_productos_id_seq', 40370, true);


--
-- TOC entry 5133 (class 0 OID 0)
-- Dependencies: 240
-- Name: archivos_generados_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.archivos_generados_id_seq', 2, true);


--
-- TOC entry 5134 (class 0 OID 0)
-- Dependencies: 230
-- Name: bodegas_producto_por_cliente_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.bodegas_producto_por_cliente_id_seq', 19614, true);


--
-- TOC entry 5135 (class 0 OID 0)
-- Dependencies: 232
-- Name: bodegas_producto_por_sucursal_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.bodegas_producto_por_sucursal_id_seq', 23, true);


--
-- TOC entry 5136 (class 0 OID 0)
-- Dependencies: 224
-- Name: clientes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.clientes_id_seq', 3, true);


--
-- TOC entry 5137 (class 0 OID 0)
-- Dependencies: 234
-- Name: configuracion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.configuracion_id_seq', 7, true);


--
-- TOC entry 5138 (class 0 OID 0)
-- Dependencies: 244
-- Name: correos_procesados_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.correos_procesados_id_seq', 2, true);


--
-- TOC entry 5139 (class 0 OID 0)
-- Dependencies: 221
-- Name: pedido_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pedido_items_id_seq', 6902, true);


--
-- TOC entry 5140 (class 0 OID 0)
-- Dependencies: 219
-- Name: pedidos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pedidos_id_seq', 388, true);


--
-- TOC entry 5141 (class 0 OID 0)
-- Dependencies: 223
-- Name: pedidos_numero_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pedidos_numero_seq', 32, true);


--
-- TOC entry 5142 (class 0 OID 0)
-- Dependencies: 246
-- Name: producto_alias_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.producto_alias_id_seq', 1718, true);


--
-- TOC entry 5143 (class 0 OID 0)
-- Dependencies: 228
-- Name: productos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.productos_id_seq', 3111, true);


--
-- TOC entry 5144 (class 0 OID 0)
-- Dependencies: 226
-- Name: sucursales_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sucursales_id_seq', 738, true);


--
-- TOC entry 5145 (class 0 OID 0)
-- Dependencies: 242
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 3, true);


--
-- TOC entry 4889 (class 2606 OID 40974)
-- Name: alias_productos alias_productos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alias_productos
    ADD CONSTRAINT alias_productos_pkey PRIMARY KEY (id);


--
-- TOC entry 4893 (class 2606 OID 49227)
-- Name: archivos_generados archivos_generados_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.archivos_generados
    ADD CONSTRAINT archivos_generados_pkey PRIMARY KEY (id);


--
-- TOC entry 4874 (class 2606 OID 24645)
-- Name: bodegas_producto_por_cliente bodegas_producto_por_cliente_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bodegas_producto_por_cliente
    ADD CONSTRAINT bodegas_producto_por_cliente_pkey PRIMARY KEY (id);


--
-- TOC entry 4879 (class 2606 OID 24665)
-- Name: bodegas_producto_por_sucursal bodegas_producto_por_sucursal_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bodegas_producto_por_sucursal
    ADD CONSTRAINT bodegas_producto_por_sucursal_pkey PRIMARY KEY (id);


--
-- TOC entry 4862 (class 2606 OID 24585)
-- Name: clientes clientes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clientes
    ADD CONSTRAINT clientes_pkey PRIMARY KEY (id);


--
-- TOC entry 4884 (class 2606 OID 32784)
-- Name: configuracion configuracion_clave_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configuracion
    ADD CONSTRAINT configuracion_clave_key UNIQUE (clave);


--
-- TOC entry 4886 (class 2606 OID 32782)
-- Name: configuracion configuracion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.configuracion
    ADD CONSTRAINT configuracion_pkey PRIMARY KEY (id);


--
-- TOC entry 4904 (class 2606 OID 82011)
-- Name: correos_procesados correos_procesados_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correos_procesados
    ADD CONSTRAINT correos_procesados_pkey PRIMARY KEY (id);


--
-- TOC entry 4906 (class 2606 OID 82013)
-- Name: correos_procesados correos_procesados_uid_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.correos_procesados
    ADD CONSTRAINT correos_procesados_uid_key UNIQUE (uid);


--
-- TOC entry 4860 (class 2606 OID 16404)
-- Name: pedido_items pedido_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedido_items
    ADD CONSTRAINT pedido_items_pkey PRIMARY KEY (id);


--
-- TOC entry 4856 (class 2606 OID 16395)
-- Name: pedidos pedidos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_pkey PRIMARY KEY (id);


--
-- TOC entry 4914 (class 2606 OID 106563)
-- Name: producto_alias producto_alias_cliente_id_producto_id_alias_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.producto_alias
    ADD CONSTRAINT producto_alias_cliente_id_producto_id_alias_key UNIQUE (cliente_id, producto_id, alias);


--
-- TOC entry 4916 (class 2606 OID 106561)
-- Name: producto_alias producto_alias_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.producto_alias
    ADD CONSTRAINT producto_alias_pkey PRIMARY KEY (id);


--
-- TOC entry 4872 (class 2606 OID 24615)
-- Name: productos productos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.productos
    ADD CONSTRAINT productos_pkey PRIMARY KEY (id);


--
-- TOC entry 4870 (class 2606 OID 24598)
-- Name: sucursales sucursales_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sucursales
    ADD CONSTRAINT sucursales_pkey PRIMARY KEY (id);


--
-- TOC entry 4877 (class 2606 OID 24647)
-- Name: bodegas_producto_por_cliente uq_bod_cli; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bodegas_producto_por_cliente
    ADD CONSTRAINT uq_bod_cli UNIQUE (cliente_id, producto_id);


--
-- TOC entry 4882 (class 2606 OID 24667)
-- Name: bodegas_producto_por_sucursal uq_bod_suc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bodegas_producto_por_sucursal
    ADD CONSTRAINT uq_bod_suc UNIQUE (sucursal_id, producto_id);


--
-- TOC entry 4865 (class 2606 OID 24587)
-- Name: clientes uq_clientes_ruc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clientes
    ADD CONSTRAINT uq_clientes_ruc UNIQUE (ruc);


--
-- TOC entry 4900 (class 2606 OID 81994)
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- TOC entry 4902 (class 2606 OID 81996)
-- Name: usuarios usuarios_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_username_key UNIQUE (username);


--
-- TOC entry 4890 (class 1259 OID 40986)
-- Name: idx_alias_productos_cliente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_alias_productos_cliente ON public.alias_productos USING btree (cliente_id);


--
-- TOC entry 4894 (class 1259 OID 49230)
-- Name: idx_archivos_estado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archivos_estado ON public.archivos_generados USING btree (estado);


--
-- TOC entry 4895 (class 1259 OID 49228)
-- Name: idx_archivos_fecha_generacion; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archivos_fecha_generacion ON public.archivos_generados USING btree (fecha_generacion);


--
-- TOC entry 4896 (class 1259 OID 49229)
-- Name: idx_archivos_tipo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_archivos_tipo ON public.archivos_generados USING btree (tipo_archivo);


--
-- TOC entry 4875 (class 1259 OID 24658)
-- Name: idx_bod_cli_cliente_prod; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bod_cli_cliente_prod ON public.bodegas_producto_por_cliente USING btree (cliente_id, producto_id);


--
-- TOC entry 4880 (class 1259 OID 24678)
-- Name: idx_bod_suc_sucursal_prod; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_bod_suc_sucursal_prod ON public.bodegas_producto_por_sucursal USING btree (sucursal_id, producto_id);


--
-- TOC entry 4887 (class 1259 OID 32785)
-- Name: idx_configuracion_clave; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_configuracion_clave ON public.configuracion USING btree (clave);


--
-- TOC entry 4907 (class 1259 OID 82015)
-- Name: idx_correos_procesados_fecha; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_correos_procesados_fecha ON public.correos_procesados USING btree (fecha_procesado);


--
-- TOC entry 4908 (class 1259 OID 82014)
-- Name: idx_correos_procesados_uid; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_correos_procesados_uid ON public.correos_procesados USING btree (uid);


--
-- TOC entry 4857 (class 1259 OID 16411)
-- Name: idx_items_pedido_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_items_pedido_id ON public.pedido_items USING btree (pedido_id);


--
-- TOC entry 4858 (class 1259 OID 16412)
-- Name: idx_items_sku; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_items_sku ON public.pedido_items USING btree (sku);


--
-- TOC entry 4851 (class 1259 OID 32770)
-- Name: idx_pedidos_estado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pedidos_estado ON public.pedidos USING btree (estado);


--
-- TOC entry 4852 (class 1259 OID 32771)
-- Name: idx_pedidos_fecha_estado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pedidos_fecha_estado ON public.pedidos USING btree (fecha DESC, estado);


--
-- TOC entry 4853 (class 1259 OID 16410)
-- Name: idx_pedidos_numero; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pedidos_numero ON public.pedidos USING btree (numero_pedido);


--
-- TOC entry 4854 (class 1259 OID 57394)
-- Name: idx_pedidos_orden_compra; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pedidos_orden_compra ON public.pedidos USING btree (orden_compra) WHERE (orden_compra IS NOT NULL);


--
-- TOC entry 4909 (class 1259 OID 106576)
-- Name: idx_producto_alias_alias; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_producto_alias_alias ON public.producto_alias USING btree (alias);


--
-- TOC entry 4910 (class 1259 OID 106575)
-- Name: idx_producto_alias_cliente_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_producto_alias_cliente_id ON public.producto_alias USING btree (cliente_id);


--
-- TOC entry 4911 (class 1259 OID 106577)
-- Name: idx_producto_alias_cliente_producto; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_producto_alias_cliente_producto ON public.producto_alias USING btree (cliente_id, producto_id);


--
-- TOC entry 4912 (class 1259 OID 106574)
-- Name: idx_producto_alias_producto_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_producto_alias_producto_id ON public.producto_alias USING btree (producto_id);


--
-- TOC entry 4866 (class 1259 OID 65584)
-- Name: idx_sucursales_ciudad; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sucursales_ciudad ON public.sucursales USING btree (ciudad) WHERE (ciudad IS NOT NULL);


--
-- TOC entry 4867 (class 1259 OID 24605)
-- Name: idx_sucursales_cliente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sucursales_cliente ON public.sucursales USING btree (cliente_id);


--
-- TOC entry 4868 (class 1259 OID 49235)
-- Name: idx_sucursales_ruc; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sucursales_ruc ON public.sucursales USING btree (ruc) WHERE (ruc IS NOT NULL);


--
-- TOC entry 4897 (class 1259 OID 81998)
-- Name: idx_usuarios_activo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_usuarios_activo ON public.usuarios USING btree (activo);


--
-- TOC entry 4898 (class 1259 OID 81997)
-- Name: idx_usuarios_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_usuarios_username ON public.usuarios USING btree (username);


--
-- TOC entry 4891 (class 1259 OID 40985)
-- Name: uq_alias_prod_cliente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_alias_prod_cliente ON public.alias_productos USING btree (cliente_id, producto_id);


--
-- TOC entry 4863 (class 1259 OID 24588)
-- Name: uq_clientes_nombre_ci; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_clientes_nombre_ci ON public.clientes USING btree (upper(nombre));


--
-- TOC entry 4930 (class 2620 OID 40988)
-- Name: alias_productos trigger_actualizar_alias_productos; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trigger_actualizar_alias_productos BEFORE UPDATE ON public.alias_productos FOR EACH ROW EXECUTE FUNCTION public.actualizar_fecha_modificacion_alias();


--
-- TOC entry 4931 (class 2620 OID 49232)
-- Name: archivos_generados trigger_actualizar_archivos_generados; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trigger_actualizar_archivos_generados BEFORE UPDATE ON public.archivos_generados FOR EACH ROW EXECUTE FUNCTION public.actualizar_fecha_modificacion();


--
-- TOC entry 4926 (class 2606 OID 40980)
-- Name: alias_productos alias_productos_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alias_productos
    ADD CONSTRAINT alias_productos_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.clientes(id) ON DELETE CASCADE;


--
-- TOC entry 4927 (class 2606 OID 40975)
-- Name: alias_productos alias_productos_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alias_productos
    ADD CONSTRAINT alias_productos_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id) ON DELETE CASCADE;


--
-- TOC entry 4922 (class 2606 OID 24648)
-- Name: bodegas_producto_por_cliente bodegas_producto_por_cliente_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bodegas_producto_por_cliente
    ADD CONSTRAINT bodegas_producto_por_cliente_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.clientes(id) ON DELETE CASCADE;


--
-- TOC entry 4923 (class 2606 OID 24653)
-- Name: bodegas_producto_por_cliente bodegas_producto_por_cliente_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bodegas_producto_por_cliente
    ADD CONSTRAINT bodegas_producto_por_cliente_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id) ON DELETE CASCADE;


--
-- TOC entry 4924 (class 2606 OID 24673)
-- Name: bodegas_producto_por_sucursal bodegas_producto_por_sucursal_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bodegas_producto_por_sucursal
    ADD CONSTRAINT bodegas_producto_por_sucursal_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id) ON DELETE CASCADE;


--
-- TOC entry 4925 (class 2606 OID 24668)
-- Name: bodegas_producto_por_sucursal bodegas_producto_por_sucursal_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bodegas_producto_por_sucursal
    ADD CONSTRAINT bodegas_producto_por_sucursal_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id) ON DELETE CASCADE;


--
-- TOC entry 4919 (class 2606 OID 16405)
-- Name: pedido_items pedido_items_pedido_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedido_items
    ADD CONSTRAINT pedido_items_pedido_id_fkey FOREIGN KEY (pedido_id) REFERENCES public.pedidos(id) ON DELETE CASCADE;


--
-- TOC entry 4920 (class 2606 OID 82037)
-- Name: pedido_items pedido_items_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedido_items
    ADD CONSTRAINT pedido_items_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id) ON DELETE SET NULL;


--
-- TOC entry 4917 (class 2606 OID 24679)
-- Name: pedidos pedidos_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.clientes(id) ON DELETE SET NULL;


--
-- TOC entry 4918 (class 2606 OID 24684)
-- Name: pedidos pedidos_sucursal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pedidos
    ADD CONSTRAINT pedidos_sucursal_id_fkey FOREIGN KEY (sucursal_id) REFERENCES public.sucursales(id) ON DELETE SET NULL;


--
-- TOC entry 4928 (class 2606 OID 106569)
-- Name: producto_alias producto_alias_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.producto_alias
    ADD CONSTRAINT producto_alias_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.clientes(id) ON DELETE CASCADE;


--
-- TOC entry 4929 (class 2606 OID 106564)
-- Name: producto_alias producto_alias_producto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.producto_alias
    ADD CONSTRAINT producto_alias_producto_id_fkey FOREIGN KEY (producto_id) REFERENCES public.productos(id) ON DELETE CASCADE;


--
-- TOC entry 4921 (class 2606 OID 24599)
-- Name: sucursales sucursales_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sucursales
    ADD CONSTRAINT sucursales_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.clientes(id) ON DELETE CASCADE;


-- Completed on 2025-10-24 11:53:09

--
-- PostgreSQL database dump complete
--

\unrestrict 1ykv42dMBxVxLR2Ahf4A7vCrKmNOQ5gEjZaAaYChdRevnDl9ITrM8oWfuFaZecz

