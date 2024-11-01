import cv2

def draw_menu(hud, image, avg_temp, threshold, cmapText, rad, scale, alpha, snaptime, responses, elapsed):
    if not hud:
        return

    # display black box for our data
    cv2.rectangle(image, (0, 0), (160, 120), (0, 0, 0), -1)
    # put text in the box
    draw_text(image, 'Avg Temp: {} C'.format(avg_temp), 10, 14)
    draw_text(image, 'Label Threshold: {} C'.format(threshold), 10, 28)
    draw_text(image, 'Colormap: {}'.format(cmapText), 10, 42)
    draw_text(image, 'Blur: {}'.format(rad), 10, 56)
    draw_text(image, 'Scaling: {}'.format(scale), 10, 70)
    draw_text(image, 'Contrast: {}'.format(alpha), 10, 84)
    draw_text(image, 'Snapshot: {}'.format(snaptime), 10, 98)
    draw_text(image, 'Recording: ' + elapsed, 10, 112, color=((40, 40, 255) if responses else (200, 200, 200)))

def draw_text(img, text, x, y, contrast = False, color: tuple = (255, 255, 255)):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.45

    if(contrast):
        cv2.putText(img, text, (x, y), font, font_scale, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(img, text, (x, y), font, font_scale, (0, 255, 255), 1, cv2.LINE_AA)
    else:
        cv2.putText(img, text, (x, y), font, font_scale, color, 1, cv2.LINE_AA)

def draw_crosshair(img, temp, width, height):
    bar_length = 20

    center_ver = int(height / 2)
    center_hor = int(width / 2)

    top = (center_hor, center_ver + bar_length)
    bottom = (center_hor, center_ver - bar_length)
    left = (center_hor - bar_length, center_ver)
    right = (center_hor + bar_length, center_ver)

    cv2.line(img, top, bottom, (255, 255, 255), 2)  # vline
    cv2.line(img, right, left, (255, 255, 255), 2)  # hline

    cv2.line(img, top, bottom, (0, 0, 0), 1)  # vline
    cv2.line(img, right, left, (0, 0, 0), 1)  # hline

    draw_text(img, '{}: C'.format(str(temp)), int(width / 2) + 10, int(height / 2) - 10, True)

def draw_box(img, left, right, bottom, top):
    cv2.line(img, (left, bottom), (right, bottom), (0, 0, 0), 2)
    cv2.line(img, (right, bottom), (right, top), (0, 0, 0), 2)
    cv2.line(img, (right, top), (left, top), (0, 0, 0), 2)
    cv2.line(img, (left, top), (left, bottom), (0, 0, 0), 2)

def draw_dot(img, col, row, scale, color, temp):
    s_col = col * scale
    s_row = row * scale
    cv2.circle(img, (s_col, s_row), 5, (0, 0, 0), 2)
    cv2.circle(img, (s_col, s_row), 5, color, -1)

    draw_text(img, '{} C'.format(temp), s_col + 10, s_row + 5, True)

def draw_zone(image, zone, th_data, scale):
    zone.set_th_data(th_data)
    z_l_col, z_l_row, z_min_temp = zone.find_lowest()
    z_m_col, z_m_row, z_max_temp = zone.find_highest()

    draw_dot(image, z_l_col + zone.left, z_l_row + zone.bottom, scale, (255, 0, 0), z_min_temp)
    draw_dot(image, z_m_col + zone.left, z_m_row + zone.bottom, scale, (0, 0, 255), z_max_temp)
    draw_box(image, zone.left * scale, zone.right * scale, zone.bottom * scale, zone.top * scale)
    draw_text(image, "Avg {} : {}C".format(zone.name, zone.find_average()), zone.left * scale,
                  zone.bottom * scale + 15, color=(0, 255, 0), contrast=True)