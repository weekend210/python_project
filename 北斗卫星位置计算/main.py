import numpy
import math

u = 398600500000000
we = 7.2921151467e-5
l1 = 1575.42
c = 3.0e8


# 计算偏近点角E
def computeE(M, e):
    E = 0.0
    E1 = 1.0
    count = 0
    while abs(E1 - E) > 1e-10:
        count = count + 1
        E1 = E
        E = M + e * math.sin(E)
        if count > 1e8:
            print("计算偏近点角时未收敛！")
            break

    return E


def x_y_z(sqrt_A, dn, M0, t, toe, e, omega, Cuc, Cus, Crc, Crs, Cic, Cis, i0, IDOT, OMEGA_A0, OMEGA_DOT):
    # 计算观测瞬间卫星平近点角M
    n0 = numpy.sqrt(u) / numpy.power(sqrt_A, 3)  # 参考时刻TOE平均角速度n0
    n = n0 + dn  # 时刻未定的平均角速度n
    # print('平均角速度n=', n)

    M = M0 + n * (t - toe)
    # print('观测瞬间卫星的平近点角M=', M)

    # 计算偏近点角E
    E = computeE(M, e)
    # print('偏近点角E=', E)

    # 计算升角距角θ'
    # f = math.atan((numpy.sqrt((1.0 - e * e)) * math.sin(E)) / (math.cos(E) - e))
    f = 2 * math.atan(numpy.sqrt((1 + e) / (1 - e)) * math.tan(E / 2))
    # print('真近点角F=', f)
    _theta = f + omega
    # print('升交距角u’=', _theta)

    g_theta = Cuc * math.cos(2 * _theta) + Cus * math.sin(2 * _theta)
    g_r = Crc * math.cos(2 * _theta) + Crs * math.sin(2 * _theta)
    g_i = Cic * math.cos(2 * _theta) + Cis * math.sin(2 * _theta)

    # print('摄动改正项')
    # print('gu=', g_theta)
    # print('gr=', g_r)
    # print('gi=', g_i)

    # 进行摄动改正
    theta = _theta + g_theta
    r = sqrt_A * sqrt_A * (1.0 - e * math.cos(E)) + g_r
    i = i0 + g_i + IDOT * (t - toe)
    # print('摄动改正值')
    # print('u=', theta)
    # print('r=', r)
    # print('i=', i)

    # 计算卫星在轨道面坐标系中的位置
    x = r * math.cos(theta)
    y = r * math.sin(theta)
    # print('x=', x)
    # print('y=', y)

    # 计算观测瞬间升交点精度
    L = OMEGA_A0 + OMEGA_DOT * (t - toe) - we * t
    # print('L=', L)

    # 计算卫星的空间直角坐标
    X1 = x * math.cos(L) - y * math.sin(L) * math.cos(i)
    Y1 = x * math.sin(L) + y * math.cos(L) * math.cos(i)
    Z1 = y * math.sin(i)
    return X1, Y1, Z1


def Doppler(x1, y1, z1, x2, y2, z2, xr, yr, zr, t):
    d1 = numpy.sqrt(numpy.power(x1 - xr, 2) + numpy.power(y1 - yr, 2) + numpy.power(z1 - zr, 2))
    d2 = numpy.sqrt(numpy.power(x2 - xr, 2) + numpy.power(y2 - yr, 2) + numpy.power(z2 - zr, 2))

    vd = abs(d1 - d2) / t

    fd = vd * l1 / c

    return fd


if __name__ == '__main__':
    # 根据星历计算位置
    t = 0
    write_data = ''
    for i in range(150):
        try:
            with open(f"./GNSS_DATA/Eph{i}.txt", "r") as f:
                data = f.read().split('\n')
        except:
            pass
            continue

        satellite_data = {}
        for j in data:
            if j == '':
                continue
            parameter = j.split(': ')
            satellite_data[parameter[0]] = float(parameter[1])
        X1, Y1, Z1 = x_y_z(satellite_data['sqrta'], satellite_data['deltaN'], satellite_data['M0'], t,
                           satellite_data['toe'], satellite_data['e'], satellite_data['w0'], satellite_data['Cuc'],
                           satellite_data['Cus'], satellite_data['Crc'], satellite_data['Crs'], satellite_data['Cic'],
                           satellite_data['Cis'], satellite_data['i0'], satellite_data['di/dt'],
                           satellite_data['Omega0'], satellite_data['OmegaDot'])
        write_str = 'svid:' + str(int(satellite_data['svid'])) + '\t' + 'x:' + str(X1) + '\t' + 'y:' + str(Y1) + '\t' + 'z:' + str(Z1) + '\n'
        write_data += write_str
    with open("position_result.txt", "w") as f:
        f.write(write_data)

    # 计算多普勒频移
    x1 = 13048070.80
    y1 = 22985904.26
    z1 = 3029314.70

    x2 = 13047980.41
    y2 = 22987819.60
    z2 = 3022987.33

    xr = -2159958.90
    yr = 4303924.34
    zr = 4084575.40

    fd = Doppler(x1, y1, z1, x2, y2, z2, xr, yr, zr, 3)
    print(fd)
