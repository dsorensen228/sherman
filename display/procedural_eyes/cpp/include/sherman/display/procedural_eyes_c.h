#ifndef SHERMAN_DISPLAY_PROCEDURAL_EYES_C_H_
#define SHERMAN_DISPLAY_PROCEDURAL_EYES_C_H_

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct sherman_eye_renderer sherman_eye_renderer;

typedef enum sherman_eye_expression {
  SHERMAN_EYE_CALM = 0,
  SHERMAN_EYE_CURIOUS = 1,
  SHERMAN_EYE_FOCUSED = 2,
  SHERMAN_EYE_PLEASED = 3,
  SHERMAN_EYE_UNCERTAIN = 4,
  SHERMAN_EYE_FRUSTRATED = 5,
  SHERMAN_EYE_TIRED = 6,
  SHERMAN_EYE_SURPRISED = 7,
} sherman_eye_expression;

typedef struct sherman_eye_inputs {
  // Integer rather than enum storage keeps invalid external values defined
  // until the implementation has validated them.
  int32_t expression;
  float gaze_x;
  float gaze_y;
  float blink;
  float attention;
  float arousal;
} sherman_eye_inputs;

// The default renderer is 320x170, purple 0xB33F on black. Functions never
// throw across the C boundary. A null create result indicates invalid size or
// allocation failure.
sherman_eye_renderer* sherman_eye_renderer_create(void);
sherman_eye_renderer* sherman_eye_renderer_create_custom(
    size_t width,
    size_t height,
    uint16_t eye_rgb565,
    uint16_t background_rgb565);
void sherman_eye_renderer_destroy(sherman_eye_renderer* renderer);

size_t sherman_eye_renderer_width(const sherman_eye_renderer* renderer);
size_t sherman_eye_renderer_height(const sherman_eye_renderer* renderer);
size_t sherman_eye_renderer_byte_size(const sherman_eye_renderer* renderer);

// Returns 0 on success, 1 for a null/invalid argument, 2 for an invalid
// expression value, or 3 for another internal failure. Values outside the
// documented continuous ranges are bounded by the renderer.
int sherman_eye_renderer_render_rgb565_be(
    const sherman_eye_renderer* renderer,
    const sherman_eye_inputs* inputs,
    uint8_t* output,
    size_t output_capacity);

// Renders the public 43-float procedural-face pose directly. This entry point
// lets a clock-owning animation layer preserve smooth pose interpolation while
// the renderer remains clock- and allocation-free.
int sherman_eye_renderer_render_pose_rgb565_be(
    const sherman_eye_renderer* renderer,
    const float* pose,
    size_t pose_count,
    uint8_t* output,
    size_t output_capacity);

#ifdef __cplusplus
}  // extern "C"
#endif

#endif  // SHERMAN_DISPLAY_PROCEDURAL_EYES_C_H_
