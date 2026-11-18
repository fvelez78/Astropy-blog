"""Figura de la ocultación lunar de Antares — cuatro paneles."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
from Ocultacion_fresnel import (occultation_curve, integrate_detector,
                                fresnel_scale, MAS, D_MOON, V_SHADOW,
                                THETA_ANTARES, THETA_REGULUS, LAMBDA0, BAND)

rcParams['font.family'] = 'DejaVu Sans'
rcParams['axes.linewidth'] = 0.8
rcParams['mathtext.fontset'] = 'dejavusans'

F = fresnel_scale()

# eje espacial y temporal
x = np.linspace(-160, 160, 6000)          # m respecto al borde geométrico
t = x / V_SHADOW * 1e3                    # ms (positivo = aún iluminado)

C_ANT   = '#C1272D'
C_REG   = '#1F6FB4'
C_PT    = '#6E6E6E'
C_ACC   = '#D98C00'

fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.2))
fig.suptitle('Ocultación lunar de Antares — difracción de Fresnel en el limbo',
             fontsize=15, fontweight='bold', y=0.975)
fig.text(0.5, 0.938,
         f'$\\lambda$ = 550 nm  ·  D = 384 400 km  ·  escala de Fresnel '
         f'$\\sqrt{{\\lambda D/2}}$ = {F:.1f} m  ·  velocidad de sombra = {V_SHADOW:.0f} m/s',
         ha='center', fontsize=10, color='#444444')

# ---------------------------------------------------------------- PANEL A
ax = axes[0, 0]
pt  = occultation_curve(x, 0)
ant = occultation_curve(x, THETA_ANTARES)
reg = occultation_curve(x, THETA_REGULUS)

ax.plot(t, pt,  color=C_PT,  lw=1.0, ls='--', label='Fuente puntual (ideal)')
ax.plot(t, reg, color=C_REG, lw=1.6, label=f'Régulo  ($\\theta$ = {THETA_REGULUS} mas)')
ax.plot(t, ant, color=C_ANT, lw=2.4, label=f'Antares  ($\\theta$ = {THETA_ANTARES} mas)')
ax.axvline(0, color='k', lw=0.7, alpha=0.35)
ax.axhline(0.25, color='k', lw=0.6, ls=':', alpha=0.5)
ax.text(-152, 0.29, 'I = 0.25 en el borde geométrico', fontsize=8, color='#444444')
ax.annotate('', xy=(-THETA_ANTARES*MAS*D_MOON/2/V_SHADOW*1e3, 1.42),
            xytext=(THETA_ANTARES*MAS*D_MOON/2/V_SHADOW*1e3, 1.42),
            arrowprops=dict(arrowstyle='<->', color=C_ANT, lw=1.3))
_s_ant = THETA_ANTARES*MAS*D_MOON
ax.text(0, 1.47, f'disco de Antares = {_s_ant:.0f} m = {_s_ant/V_SHADOW*1e3:.0f} ms',
        ha='center', fontsize=8.5, color=C_ANT)
ax.set_xlim(-160, 160); ax.set_ylim(0, 1.62)
ax.set_xlabel('Tiempo respecto al borde geométrico  (ms)')
ax.set_ylabel('Intensidad relativa')
ax.set_title('A · El tamaño del disco borra las franjas', fontsize=11.5, loc='left',
             fontweight='bold')
ax.legend(fontsize=9, loc='lower right', framealpha=0.95)
ax.grid(alpha=0.18, lw=0.6)

# ---------------------------------------------------------------- PANEL B
ax = axes[0, 1]
thetas = [0, 5, 10, 20, 41, 60]
cmap = plt.cm.plasma(np.linspace(0.05, 0.82, len(thetas)))
for th, col in zip(thetas, cmap):
    c = occultation_curve(x, th)
    lw = 2.4 if th == 41 else 1.4
    lbl = f'{th} mas' + ('  ← Antares' if th == 41 else ('  (puntual)' if th == 0 else ''))
    ax.plot(t, c, color=col, lw=lw, label=lbl)
ax.axvline(0, color='k', lw=0.7, alpha=0.35)
ax.set_xlim(-120, 120); ax.set_ylim(0, 1.55)
ax.set_xlabel('Tiempo respecto al borde geométrico  (ms)')
ax.set_ylabel('Intensidad relativa')
ax.set_title('B · El principio de la medida: cada diámetro da una curva distinta',
             fontsize=11.5, loc='left', fontweight='bold')
ax.legend(fontsize=8.5, loc='lower right', title='$\\theta$', title_fontsize=9,
          framealpha=0.95)
ax.grid(alpha=0.18, lw=0.6)

# ---------------------------------------------------------------- PANEL C
ax = axes[1, 0]
ant_band = occultation_curve(x, THETA_ANTARES, band=BAND)
for t_int, col, ls in [(0.001, C_ANT, '-'), (0.010, '#E07B39', '-'),
                       (0.025, '#3D8B6B', '-'), (0.040, '#7B4EA8', '-')]:
    c = integrate_detector(x, ant_band, t_int)
    lbl = f'{t_int*1e3:.0f} ms'
    if abs(t_int - 0.025) < 1e-9:
        lbl += '  (vídeo PAL, 40 fps)'
    if abs(t_int - 0.001) < 1e-9:
        lbl += '  (1 kHz)'
    ax.plot(t, c, color=col, lw=2.0 if t_int <= 0.001 else 1.5, ls=ls, label=lbl)
ax.axvline(0, color='k', lw=0.7, alpha=0.35)
ax.set_xlim(-140, 140); ax.set_ylim(0, 1.25)
ax.set_xlabel('Tiempo respecto al borde geométrico  (ms)')
ax.set_ylabel('Intensidad relativa')
ax.set_title('C · Antares en banda V: el muestreo del detector', fontsize=11.5,
             loc='left', fontweight='bold')
ax.legend(fontsize=8.5, loc='lower right', title='Tiempo de integración',
          title_fontsize=9, framealpha=0.95)
ax.grid(alpha=0.18, lw=0.6)
ax.text(-135, 1.13, 'La caída 10→90 % dura ~87 ms: incluso a 25 ms\nel perfil del disco se conserva bien.',
        fontsize=8.5, color='#444444', va='top')

# ---------------------------------------------------------------- PANEL D
ax = axes[1, 1]
unif = occultation_curve(x, THETA_ANTARES, band=BAND, limb_dark=0.0)
ld   = occultation_curve(x, THETA_ANTARES, band=BAND, limb_dark=0.8)
ax.plot(t, unif, color=C_ANT, lw=2.2, label='Disco uniforme')
ax.plot(t, ld, color=C_ACC, lw=2.2, ls='--', label='Con oscurecimiento de limbo ($u$ = 0.8)')
ax.axvline(0, color='k', lw=0.7, alpha=0.35)
ax.set_xlim(-110, 110); ax.set_ylim(0, 1.18)
ax.set_xlabel('Tiempo respecto al borde geométrico  (ms)')
ax.set_ylabel('Intensidad relativa')
ax.set_title('D · Lo que queda por medir: el perfil del disco', fontsize=11.5,
             loc='left', fontweight='bold')
ax.legend(fontsize=9, loc='lower right', framealpha=0.95)
ax.grid(alpha=0.18, lw=0.6)

axr = ax.twinx()
diff = (ld - unif) * 100
axr.plot(t, diff, color='#2E7D32', lw=1.2, alpha=0.85)
axr.set_ylabel('Diferencia (% del flujo)', color='#2E7D32', fontsize=9)
axr.tick_params(axis='y', labelcolor='#2E7D32', labelsize=8)
axr.set_ylim(-14, 14)
axr.axhline(0, color='#2E7D32', lw=0.5, alpha=0.4)
print(f'Diferencia máxima uniforme vs limbo oscurecido: {np.abs(diff).max():.1f} %')

fig.tight_layout(rect=[0, 0.01, 1, 0.925])
fig.savefig('antares_ocultacion.png', dpi=170, facecolor='white')
print('Figura guardada.')

# --------------------------------------------------------- números clave
s_ant = THETA_ANTARES * MAS * D_MOON
print(f'\nAntares: {s_ant:.1f} m = {s_ant/F:.2f} escalas de Fresnel')
print(f'Duración de la caída (10%-90%):', end=' ')
lo = np.interp(0.1, ant[::-1], t[::-1]); hi = np.interp(0.9, ant[::-1], t[::-1])
print(f'{abs(hi-lo):.1f} ms')
lo2 = np.interp(0.1, reg[::-1], t[::-1]); hi2 = np.interp(0.9, reg[::-1], t[::-1])
print(f'Régulo, misma medida: {abs(hi2-lo2):.1f} ms')
print(f'Contraste 1er máximo — puntual: {pt.max():.3f} | Régulo: {reg.max():.3f} | Antares: {ant.max():.3f}')