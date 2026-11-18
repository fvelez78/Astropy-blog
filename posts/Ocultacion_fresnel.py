"""
Ocultación lunar de Antares — simulación de difracción de Fresnel
=================================================================
Modela la curva de luz de una estrella ocultada por el limbo lunar.

Física:
  1. El limbo lunar actúa como un filo de cuchillo semi-infinito (la Luna no
     tiene atmósfera, así que el borde es abrupto).
  2. Una fuente PUNTUAL produce difracción de Fresnel:
        I(v)/I0 = 0.5 * [ (C(v)+1/2)^2 + (S(v)+1/2)^2 ]
     con v = x * sqrt(2/(lambda*D)), y C,S las integrales de Fresnel.
  3. Una estrella RESUELTA es un conjunto incoherente de puntos: la curva
     observada es la convolución del patrón puntual con el perfil de brillo
     de la estrella proyectado sobre la dirección de movimiento.
  4. Efectos instrumentales: ancho de banda finito (mezcla escalas de Fresnel)
     y tiempo de integración del detector (promedia en el tiempo).

Verificaciones analíticas: I(v=0)=0.25, primer máximo 1.370 en v=1.2172.
"""
import numpy as np
from scipy.special import fresnel

# ----------------------------------------------------------------- constantes
ARCSEC = np.pi / (180.0 * 3600.0)     # rad por segundo de arco
MAS    = ARCSEC * 1e-3                # rad por milisegundo de arco
D_MOON = 3.844e8                      # m, distancia media Tierra-Luna

# ----------------------------------------------------------------- parámetros
LAMBDA0 = 550e-9        # m, longitud de onda central (banda V)
BAND    = 88e-9         # m, ancho de banda efectivo de V (~500-600 nm)
V_SHADOW = 600.0        # m/s, velocidad de la sombra sobre el observador

# Diámetros angulares (mas). Valores aproximados de la literatura.
THETA_ANTARES = 41.0    # supergigante roja M1.5, disco muy grande
THETA_REGULUS = 1.3     # B8 rotador rápido, disco diminuto


def fresnel_scale(lam=LAMBDA0, D=D_MOON):
    """Escala de Fresnel en metros: sqrt(lambda*D/2)."""
    return np.sqrt(lam * D / 2.0)


def knife_edge(x, lam=LAMBDA0, D=D_MOON):
    """Patrón de difracción de una fuente puntual. x en metros.
    x > 0 = fuera de la sombra geométrica (en la luz)."""
    v = x * np.sqrt(2.0 / (lam * D))
    S, C = fresnel(v)
    return 0.5 * ((C + 0.5) ** 2 + (S + 0.5) ** 2)


def disk_profile(u, s_lin, limb_dark=0.0, n=400):
    """Perfil 1D de un disco estelar proyectado sobre el eje de movimiento.

    u        : posiciones (m) relativas al centro del disco
    s_lin    : DIÁMETRO lineal del disco a la distancia de la Luna (m)
    limb_dark: coeficiente lineal de oscurecimiento del limbo (0 = disco uniforme)
               I(mu)/I(1) = 1 - u_ld*(1 - mu),  mu = cos(angulo del limbo)
    Se integra numéricamente sobre la cuerda perpendicular.
    """
    R = s_lin / 2.0
    w = np.zeros_like(u, dtype=float)
    for i, ui in enumerate(u):
        if abs(ui) >= R:
            continue
        ymax = np.sqrt(R * R - ui * ui)
        y = np.linspace(-ymax, ymax, n)
        rho = np.sqrt(ui * ui + y * y) / R
        rho = np.clip(rho, 0.0, 1.0)
        mu = np.sqrt(1.0 - rho * rho)
        w[i] = np.trapezoid(1.0 - limb_dark * (1.0 - mu), y)
    tot = np.trapezoid(w, u)
    return w / tot if tot > 0 else w


def occultation_curve(x, theta_mas, lam=LAMBDA0, band=0.0, limb_dark=0.0,
                      D=D_MOON, n_lam=9):
    """Curva de luz de la ocultación.

    x         : posiciones (m) del observador respecto al borde geométrico
    theta_mas : diámetro angular de la estrella (mas). 0 = puntual
    band      : ancho de banda (m). 0 = monocromático
    """
    # --- patrón puntual, promediado sobre la banda si aplica
    if band > 0:
        lams = np.linspace(lam - band / 2, lam + band / 2, n_lam)
        base = np.mean([knife_edge(x, l, D) for l in lams], axis=0)
    else:
        base = knife_edge(x, lam, D)

    if theta_mas <= 0:
        return base

    # --- convolución con el disco estelar
    s_lin = theta_mas * MAS * D                 # diámetro lineal en metros
    dx = x[1] - x[0]
    half = int(np.ceil((s_lin / 2.0) / dx)) + 2
    u = np.arange(-half, half + 1) * dx
    w = disk_profile(u, s_lin, limb_dark)
    w = w / w.sum()
    pad = len(w) // 2
    padded = np.concatenate([np.full(pad, base[0]), base, np.full(pad, base[-1])])
    return np.convolve(padded, w, mode='valid')[:len(x)]


def integrate_detector(x, curve, t_int, v=V_SHADOW):
    """Promedia la curva sobre el tiempo de integración del detector."""
    dx = x[1] - x[0]
    npix = max(1, int(round(t_int * v / dx)))
    if npix <= 1:
        return curve
    k = np.ones(npix) / npix
    pad = npix // 2
    padded = np.concatenate([np.full(pad, curve[0]), curve, np.full(pad, curve[-1])])
    return np.convolve(padded, k, mode='same')[pad:pad + len(x)]


# ------------------------------------------------------------------ resumen
if __name__ == '__main__':
    F = fresnel_scale()
    print(f"Escala de Fresnel (550 nm):      {F:.1f} m")
    print(f"Velocidad de sombra adoptada:    {V_SHADOW:.0f} m/s")
    print(f"Periodo de franja ~ 2F:          {2*F/V_SHADOW*1e3:.1f} ms\n")
    for nm, th in [('Antares', THETA_ANTARES), ('Régulo', THETA_REGULUS)]:
        s = th * MAS * D_MOON
        print(f"{nm:9s} theta={th:5.1f} mas -> {s:6.1f} m = {s/F:5.2f} escalas "
              f"de Fresnel -> cruce en {s/V_SHADOW*1e3:6.1f} ms")