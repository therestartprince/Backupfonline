//      __________        ___               ______            _
//     / ____/ __ \____  / (_)___  ___     / ____/___  ____ _(_)___  ___
//    / /_  / / / / __ \/ / / __ \/ _ \   / __/ / __ \/ __ `/ / __ \/ _ \
//   / __/ / /_/ / / / / / / / / /  __/  / /___/ / / / /_/ / / / / /  __/
//  /_/    \____/_/ /_/_/_/_/ /_/\___/  /_____/_/ /_/\__, /_/_/ /_/\___/
//                                                  /____/
// FOnline Engine
// https://fonline.ru
// https://github.com/cvet/fonline
//
// MIT License
//
// Copyright (c) 2006 - present, Anton Tsvetinskiy aka cvet <cvet@tut.by>
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
//

#include "GenericUtils.h"
#include "Log.h"
#include "StringUtils.h"

#include "sha2.h"
#include "zlib.h"

auto Math::FloatCompare(float f1, float f2) -> bool
{
    if (std::abs(f1 - f2) <= 1.0e-5f) {
        return true;
    }
    return std::abs(f1 - f2) <= 1.0e-5f * std::max(std::abs(f1), std::abs(f2));
}

auto Hashing::MurmurHash2(const uchar* data, uint len) -> uint
{
    const uint seed = 0;
    const uint m = 0x5BD1E995;
    const auto r = 24;
    auto h = seed ^ len;

    while (len >= 4) {
        uint k = data[0];
        k |= data[1] << 8;
        k |= data[2] << 16;
        k |= data[3] << 24;

        k *= m;
        k ^= k >> r;
        k *= m;

        h *= m;
        h ^= k;

        data += 4;
        len -= 4;
    }

    switch (len) {
    case 3:
        h ^= data[2] << 16;
        [[fallthrough]];
    case 2:
        h ^= data[1] << 8;
        [[fallthrough]];
    case 1:
        h ^= data[0];
        h *= m;
        [[fallthrough]];
    default:
        break;
    }

    h ^= h >> 13;
    h *= m;
    h ^= h >> 15;
    return h;
}

auto Hashing::MurmurHash2_64(const uchar* data, uint len) -> uint64
{
    const uint seed = 0;
    const auto m = 0xc6a4a7935bd1e995ULL;
    const auto r = 47;
    auto h = seed ^ len * m;

    const auto* data2 = reinterpret_cast<const uint64*>(data);
    const auto* end = data2 + len / 8;

    while (data2 != end) {
        auto k = *data2++;

        k *= m;
        k ^= k >> r;
        k *= m;

        h ^= k;
        h *= m;
    }

    const auto* data3 = reinterpret_cast<const uchar*>(data2);

    switch (len & 7) {
    case 7:
        h ^= static_cast<uint64>(data3[6]) << 48;
        [[fallthrough]];
    case 6:
        h ^= static_cast<uint64>(data3[5]) << 40;
        [[fallthrough]];
    case 5:
        h ^= static_cast<uint64>(data3[4]) << 32;
        [[fallthrough]];
    case 4:
        h ^= static_cast<uint64>(data3[3]) << 24;
        [[fallthrough]];
    case 3:
        h ^= static_cast<uint64>(data3[2]) << 16;
        [[fallthrough]];
    case 2:
        h ^= static_cast<uint64>(data3[1]) << 8;
        [[fallthrough]];
    case 1:
        h ^= static_cast<uint64>(data3[0]);
        h *= m;
        [[fallthrough]];
    default:
        break;
    }

    h ^= h >> r;
    h *= m;
    h ^= h >> r;
    return h;
}

auto Compressor::Compress(const uchar* data, uint& data_len) -> uchar*
{
    uLongf buf_len = data_len * 110 / 100 + 12;
    auto* buf = new uchar[buf_len];

    if (compress2(buf, &buf_len, data, data_len, Z_BEST_SPEED) != Z_OK) {
        delete[] buf;
        return nullptr;
    }

    data_len = static_cast<uint>(buf_len);
    return buf;
}

auto Compressor::Compress(const vector<uchar>& data) -> vector<uchar>
{
    auto result_len = static_cast<uint>(data.size());
    auto* result = Compress(&data[0], result_len);
    if (result == nullptr) {
        return {};
    }

    vector<uchar> compressed_data;
    compressed_data.resize(result_len);
    compressed_data.shrink_to_fit();
    std::memcpy(&compressed_data[0], result, result_len);
    delete[] result;
    return compressed_data;
}

auto Compressor::Uncompress(const uchar* data, uint& data_len, uint mul_approx) -> uchar*
{
    uLongf buf_len = data_len * mul_approx;
    if (buf_len > 100000000) // 100mb
    {
        WriteLog("Unpack buffer length is too large, data length {}, multiplier {}.\n", data_len, mul_approx);
        return nullptr;
    }

    auto* buf = new uchar[buf_len];
    while (true) {
        const auto result = uncompress(buf, &buf_len, data, data_len);
        if (result == Z_BUF_ERROR) {
            buf_len *= 2;
            delete[] buf;
            buf = new uchar[buf_len];
        }
        else if (result != Z_OK) {
            delete[] buf;
            WriteLog("Unpack error {}.\n", result);
            return nullptr;
        }
        else {
            break;
        }
    }

    data_len = static_cast<uint>(buf_len);
    return buf;
}

auto Compressor::Uncompress(const vector<uchar>& data, uint mul_approx) -> vector<uchar>
{
    auto result_len = static_cast<uint>(data.size());
    auto* result = Uncompress(&data[0], result_len, mul_approx);
    if (result == nullptr) {
        return {};
    }

    vector<uchar> uncompressed_data;
    uncompressed_data.resize(result_len);
    std::memcpy(&uncompressed_data[0], result, result_len);
    delete[] result;
    return uncompressed_data;
}

// Default randomizer
static std::mt19937 RandomGenerator(std::random_device {}());
void GenericUtils::SetRandomSeed(int seed)
{
    RandomGenerator = std::mt19937(seed);
}

auto GenericUtils::Random(int minimum, int maximum) -> int
{
    return std::uniform_int_distribution {minimum, maximum}(RandomGenerator);
}

auto GenericUtils::Random(uint minimum, uint maximum) -> uint
{
    return static_cast<uint>(Random(static_cast<int>(minimum), static_cast<int>(maximum)));
}

auto GenericUtils::Percent(int full, int peace) -> int
{
    RUNTIME_ASSERT(full >= 0);

    if (full == 0) {
        return 0;
    }

    const auto percent = peace * 100 / full;
    return std::clamp(percent, 0, 100);
}

auto GenericUtils::Percent(uint full, uint peace) -> uint
{
    RUNTIME_ASSERT(full >= 0);

    if (full == 0u) {
        return 0u;
    }

    const auto percent = peace * 100u / full;
    return std::clamp(percent, 0u, 100u);
}

auto GenericUtils::NumericalNumber(uint num) -> uint
{
    if ((num & 1) != 0u) {
        return num * (num / 2 + 1);
    }

    return num * num / 2 + num / 2;
}

auto GenericUtils::IntersectCircleLine(int cx, int cy, int radius, int x1, int y1, int x2, int y2) -> bool
{
    const auto x01 = x1 - cx;
    const auto y01 = y1 - cy;
    const auto x02 = x2 - cx;
    const auto y02 = y2 - cy;
    const auto dx = x02 - x01;
    const auto dy = y02 - y01;
    const auto a = dx * dx + dy * dy;
    const auto b = 2 * (x01 * dx + y01 * dy);
    const auto c = x01 * x01 + y01 * y01 - radius * radius;
    if (-b < 0) {
        return c < 0;
    }
    if (-b < 2 * a) {
        return 4 * a * c - b * b < 0;
    }
    return a + b + c < 0;
}

auto GenericUtils::GetColorDay(const int* day_time, const uchar* colors, int game_time, int* light) -> uint
{
    uchar result[3];
    const int color_r[4] = {colors[0], colors[1], colors[2], colors[3]};
    const int color_g[4] = {colors[4], colors[5], colors[6], colors[7]};
    const int color_b[4] = {colors[8], colors[9], colors[10], colors[11]};

    game_time %= 1440;
    int time;
    int duration;
    if (game_time >= day_time[0] && game_time < day_time[1]) {
        time = 0;
        game_time -= day_time[0];
        duration = day_time[1] - day_time[0];
    }
    else if (game_time >= day_time[1] && game_time < day_time[2]) {
        time = 1;
        game_time -= day_time[1];
        duration = day_time[2] - day_time[1];
    }
    else if (game_time >= day_time[2] && game_time < day_time[3]) {
        time = 2;
        game_time -= day_time[2];
        duration = day_time[3] - day_time[2];
    }
    else {
        time = 3;
        if (game_time >= day_time[3]) {
            game_time -= day_time[3];
        }
        else {
            game_time += 1440 - day_time[3];
        }
        duration = 1440 - day_time[3] + day_time[0];
    }

    if (duration == 0) {
        duration = 1;
    }

    result[0] = static_cast<uchar>(color_r[time] + (color_r[time < 3 ? time + 1 : 0] - color_r[time]) * game_time / duration);
    result[1] = static_cast<uchar>(color_g[time] + (color_g[time < 3 ? time + 1 : 0] - color_g[time]) * game_time / duration);
    result[2] = static_cast<uchar>(color_b[time] + (color_b[time < 3 ? time + 1 : 0] - color_b[time]) * game_time / duration);

    if (light != nullptr) {
        const auto max_light = (std::max(std::max(std::max(color_r[0], color_r[1]), color_r[2]), color_r[3]) + std::max(std::max(std::max(color_g[0], color_g[1]), color_g[2]), color_g[3]) + std::max(std::max(std::max(color_b[0], color_b[1]), color_b[2]), color_b[3])) / 3;
        const auto min_light = (std::min(std::min(std::min(color_r[0], color_r[1]), color_r[2]), color_r[3]) + std::min(std::min(std::min(color_g[0], color_g[1]), color_g[2]), color_g[3]) + std::min(std::min(std::min(color_b[0], color_b[1]), color_b[2]), color_b[3])) / 3;
        const auto cur_light = (result[0] + result[1] + result[2]) / 3;

        *light = Percent(max_light - min_light, max_light - cur_light);
        *light = std::clamp(*light, 0, 100);
    }

    return result[0] << 16 | result[1] << 8 | result[2];
}

auto GenericUtils::DistSqrt(int x1, int y1, int x2, int y2) -> uint
{
    const auto dx = x1 - x2;
    const auto dy = y1 - y2;
    return static_cast<uint>(sqrt(static_cast<double>(dx * dx + dy * dy)));
}

auto GenericUtils::GetStepsXY(int x1, int y1, int x2, int y2) -> tuple<float, float>
{
    const auto dx = static_cast<float>(abs(x2 - x1));
    const auto dy = static_cast<float>(abs(y2 - y1));

    auto sx = 1.0f;
    auto sy = 1.0f;

    dx < dy ? sx = dx / dy : sy = dy / dx;

    if (x2 < x1) {
        sx = -sx;
    }
    if (y2 < y1) {
        sy = -sy;
    }

    return {sx, sy};
}

auto GenericUtils::ChangeStepsXY(float sx, float sy, float deq) -> tuple<float, float>
{
    const auto rad = deq * PI_FLOAT / 180.0f;
    sx = sx * cos(rad) - sy * sin(rad);
    sy = sx * sin(rad) + sy * cos(rad);
    return {sx, sy};
}

static void MultMatricesf(const float a[16], const float b[16], float r[16]);
static void MultMatrixVecf(const float matrix[16], const float in[4], float out[4]);
static auto InvertMatrixf(const float m[16], float inv_out[16]) -> bool;

void MatrixHelper::MatrixOrtho(float* matrix, float left, float right, float bottom, float top, float nearp, float farp)
{
    const auto r_l = right - left;
    const auto t_b = top - bottom;
    const auto f_n = farp - nearp;
    const auto tx = -(right + left) / (right - left);
    const auto ty = -(top + bottom) / (top - bottom);
    const auto tz = -(farp + nearp) / (farp - nearp);

    matrix[0] = 2.0f / r_l;
    matrix[1] = 0.0f;
    matrix[2] = 0.0f;
    matrix[3] = tx;

    matrix[4] = 0.0f;
    matrix[5] = 2.0f / t_b;
    matrix[6] = 0.0f;
    matrix[7] = ty;

    matrix[8] = 0.0f;
    matrix[9] = 0.0f;
    matrix[10] = -2.0f / f_n;
    matrix[11] = tz;

    matrix[12] = 0.0f;
    matrix[13] = 0.0f;
    matrix[14] = 0.0f;
    matrix[15] = 1.0f;
}

auto MatrixHelper::MatrixProject(float objx, float objy, float objz, const float model_matrix[16], const float proj_matrix[16], const int viewport[4], float* winx, float* winy, float* winz) -> bool
{
    float in[4];
    in[0] = objx;
    in[1] = objy;
    in[2] = objz;
    in[3] = 1.0f;

    float out[4];
    MultMatrixVecf(model_matrix, in, out);
    MultMatrixVecf(proj_matrix, out, in);
    if (in[3] == 0.0f) {
        return false;
    }

    in[0] /= in[3];
    in[1] /= in[3];
    in[2] /= in[3];

    in[0] = in[0] * 0.5f + 0.5f;
    in[1] = in[1] * 0.5f + 0.5f;
    in[2] = in[2] * 0.5f + 0.5f;

    in[0] = in[0] * static_cast<float>(viewport[2] + viewport[0]);
    in[1] = in[1] * static_cast<float>(viewport[3] + viewport[1]);

    *winx = in[0];
    *winy = in[1];
    *winz = in[2];
    return true;
}

auto MatrixHelper::MatrixUnproject(float winx, float winy, float winz, const float model_matrix[16], const float proj_matrix[16], const int viewport[4], float* objx, float* objy, float* objz) -> bool
{
    float final_matrix[16];
    MultMatricesf(model_matrix, proj_matrix, final_matrix);
    if (!InvertMatrixf(final_matrix, final_matrix)) {
        return false;
    }

    float in[4];
    in[0] = winx;
    in[1] = winy;
    in[2] = winz;
    in[3] = 1.0f;

    in[0] = (in[0] - static_cast<float>(viewport[0])) / static_cast<float>(viewport[2]);
    in[1] = (in[1] - static_cast<float>(viewport[1])) / static_cast<float>(viewport[3]);

    in[0] = in[0] * 2 - 1;
    in[1] = in[1] * 2 - 1;
    in[2] = in[2] * 2 - 1;

    float out[4];
    MultMatrixVecf(final_matrix, in, out);
    if (out[3] == 0.0f) {
        return false;
    }

    out[0] /= out[3];
    out[1] /= out[3];
    out[2] /= out[3];
    *objx = out[0];
    *objy = out[1];
    *objz = out[2];
    return true;
}

static void MultMatricesf(const float a[16], const float b[16], float r[16])
{
    for (auto i = 0; i < 4; i++) {
        for (auto j = 0; j < 4; j++) {
            r[i * 4 + j] = a[i * 4 + 0] * b[0 * 4 + j] + a[i * 4 + 1] * b[1 * 4 + j] + a[i * 4 + 2] * b[2 * 4 + j] + a[i * 4 + 3] * b[3 * 4 + j];
        }
    }
}

static void MultMatrixVecf(const float matrix[16], const float in[4], float out[4])
{
    for (auto i = 0; i < 4; i++) {
        out[i] = in[0] * matrix[0 * 4 + i] + in[1] * matrix[1 * 4 + i] + in[2] * matrix[2 * 4 + i] + in[3] * matrix[3 * 4 + i];
    }
}

static auto InvertMatrixf(const float m[16], float inv_out[16]) -> bool
{
    float inv[16];
    inv[0] = m[5] * m[10] * m[15] - m[5] * m[11] * m[14] - m[9] * m[6] * m[15] + m[9] * m[7] * m[14] + m[13] * m[6] * m[11] - m[13] * m[7] * m[10];
    inv[4] = -m[4] * m[10] * m[15] + m[4] * m[11] * m[14] + m[8] * m[6] * m[15] - m[8] * m[7] * m[14] - m[12] * m[6] * m[11] + m[12] * m[7] * m[10];
    inv[8] = m[4] * m[9] * m[15] - m[4] * m[11] * m[13] - m[8] * m[5] * m[15] + m[8] * m[7] * m[13] + m[12] * m[5] * m[11] - m[12] * m[7] * m[9];
    inv[12] = -m[4] * m[9] * m[14] + m[4] * m[10] * m[13] + m[8] * m[5] * m[14] - m[8] * m[6] * m[13] - m[12] * m[5] * m[10] + m[12] * m[6] * m[9];
    inv[1] = -m[1] * m[10] * m[15] + m[1] * m[11] * m[14] + m[9] * m[2] * m[15] - m[9] * m[3] * m[14] - m[13] * m[2] * m[11] + m[13] * m[3] * m[10];
    inv[5] = m[0] * m[10] * m[15] - m[0] * m[11] * m[14] - m[8] * m[2] * m[15] + m[8] * m[3] * m[14] + m[12] * m[2] * m[11] - m[12] * m[3] * m[10];
    inv[9] = -m[0] * m[9] * m[15] + m[0] * m[11] * m[13] + m[8] * m[1] * m[15] - m[8] * m[3] * m[13] - m[12] * m[1] * m[11] + m[12] * m[3] * m[9];
    inv[13] = m[0] * m[9] * m[14] - m[0] * m[10] * m[13] - m[8] * m[1] * m[14] + m[8] * m[2] * m[13] + m[12] * m[1] * m[10] - m[12] * m[2] * m[9];
    inv[2] = m[1] * m[6] * m[15] - m[1] * m[7] * m[14] - m[5] * m[2] * m[15] + m[5] * m[3] * m[14] + m[13] * m[2] * m[7] - m[13] * m[3] * m[6];
    inv[6] = -m[0] * m[6] * m[15] + m[0] * m[7] * m[14] + m[4] * m[2] * m[15] - m[4] * m[3] * m[14] - m[12] * m[2] * m[7] + m[12] * m[3] * m[6];
    inv[10] = m[0] * m[5] * m[15] - m[0] * m[7] * m[13] - m[4] * m[1] * m[15] + m[4] * m[3] * m[13] + m[12] * m[1] * m[7] - m[12] * m[3] * m[5];
    inv[14] = -m[0] * m[5] * m[14] + m[0] * m[6] * m[13] + m[4] * m[1] * m[14] - m[4] * m[2] * m[13] - m[12] * m[1] * m[6] + m[12] * m[2] * m[5];
    inv[3] = -m[1] * m[6] * m[11] + m[1] * m[7] * m[10] + m[5] * m[2] * m[11] - m[5] * m[3] * m[10] - m[9] * m[2] * m[7] + m[9] * m[3] * m[6];
    inv[7] = m[0] * m[6] * m[11] - m[0] * m[7] * m[10] - m[4] * m[2] * m[11] + m[4] * m[3] * m[10] + m[8] * m[2] * m[7] - m[8] * m[3] * m[6];
    inv[11] = -m[0] * m[5] * m[11] + m[0] * m[7] * m[9] + m[4] * m[1] * m[11] - m[4] * m[3] * m[9] - m[8] * m[1] * m[7] + m[8] * m[3] * m[5];
    inv[15] = m[0] * m[5] * m[10] - m[0] * m[6] * m[9] - m[4] * m[1] * m[10] + m[4] * m[2] * m[9] + m[8] * m[1] * m[6] - m[8] * m[2] * m[5];

    auto det = m[0] * inv[0] + m[1] * inv[4] + m[2] * inv[8] + m[3] * inv[12];
    if (det == 0.0f) {
        return false;
    }

    det = 1.0f / det;

    for (auto i = 0; i < 16; i++) {
        inv_out[i] = inv[i] * det;
    }
    return true;
}
