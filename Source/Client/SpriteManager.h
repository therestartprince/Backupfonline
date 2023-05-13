//      __________        ___               ______            _
//     / ____/ __ \____  / (_)___  ___     / ____/___  ____ _(_)___  ___
//    / /_  / / / / __ \/ / / __ \/ _ \   / __/ / __ \/ __ `/ / __ \/ _ `
//   / __/ / /_/ / / / / / / / / /  __/  / /___/ / / / /_/ / / / / /  __/
//  /_/    \____/_/ /_/_/_/_/ /_/\___/  /_____/_/ /_/\__, /_/_/ /_/\___/
//                                                  /____/
// FOnline Engine
// https://fonline.ru
// https://github.com/cvet/fonline
//
// MIT License
//
// Copyright (c) 2006 - 2022, Anton Tsvetinskiy aka cvet <cvet@tut.by>
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

// Todo: optimize sprite atlas filling

#pragma once

#include "Common.h"

#include "3dStuff.h"
#include "Application.h"
#include "EffectManager.h"
#include "FileSystem.h"
#include "MapSprite.h"
#include "Settings.h"
#include "VisualParticles.h"

static constexpr auto ANY_FRAMES_POOL_SIZE = 2000;
static constexpr auto MAX_STORED_PIXEL_PICKS = 100;
static constexpr auto MAX_FRAMES = 50;

// Font flags
// Todo: convert FT_ font flags to enum
static constexpr uint FT_NOBREAK = 0x0001;
static constexpr uint FT_NOBREAK_LINE = 0x0002;
static constexpr uint FT_CENTERX = 0x0004;
static constexpr uint FT_CENTERY_ENGINE = 0x1000; // Todo: fix FT_CENTERY_ENGINE workaround
static constexpr uint FT_CENTERY = 0x0008 | FT_CENTERY_ENGINE;
static constexpr uint FT_CENTERR = 0x0010;
static constexpr uint FT_BOTTOM = 0x0020;
static constexpr uint FT_UPPER = 0x0040;
static constexpr uint FT_NO_COLORIZE = 0x0080;
static constexpr uint FT_ALIGN = 0x0100;
static constexpr uint FT_BORDERED = 0x0200;
static constexpr auto FT_SKIPLINES(uint l) -> uint
{
    return 0x0400 | (l << 16);
}
static constexpr auto FT_SKIPLINES_END(uint l) -> uint
{
    return 0x0800 | (l << 16);
}

// Colors
static constexpr auto COLOR_SPRITE = COLOR_RGB(128, 128, 128);
static constexpr auto COLOR_SPRITE_RED = COLOR_SPRITE | 255 << 16;
static constexpr auto COLOR_TEXT = COLOR_RGB(60, 248, 0);
static constexpr auto COLOR_TEXT_WHITE = COLOR_RGB(255, 255, 255);
static constexpr auto COLOR_TEXT_DWHITE = COLOR_RGB(191, 191, 191);
static constexpr auto COLOR_TEXT_RED = COLOR_RGB(200, 0, 0);
static constexpr auto COLOR_SCRIPT_SPRITE(uint color) -> uint
{
    return color != 0 ? color : COLOR_SPRITE;
}
static constexpr auto COLOR_SCRIPT_TEXT(uint color) -> uint
{
    return color != 0 ? color : COLOR_TEXT;
}

enum class AtlasType
{
    Static,
    Dynamic,
    Splash,
    MeshTextures,
};

class GameTimer;

struct RenderTarget
{
    enum class SizeType
    {
        Custom,
        Screen,
        Map,
    };

    unique_ptr<RenderTexture> MainTex {};
    RenderEffect* CustomDrawEffect {};
    SizeType Size {};
    int BaseWidth {};
    int BaseHeight {};
    vector<tuple<int, int, uint>> LastPixelPicks {};
};

struct TextureAtlas
{
    struct SpaceNode
    {
        SpaceNode(int x, int y, int width, int height);
        auto FindPosition(int width, int height, int& x, int& y) -> bool;

        int PosX {};
        int PosY {};
        int Width {};
        int Height {};
        bool Busy {};
        unique_ptr<SpaceNode> Child1 {};
        unique_ptr<SpaceNode> Child2 {};
    };

    AtlasType Type {};
    RenderTarget* RTarg {};
    RenderTexture* MainTex {};
    int Width {};
    int Height {};
    unique_ptr<SpaceNode> RootNode {};
    int CurX {};
    int CurY {};
    int LineMaxH {};
    int LineCurH {};
    int LineW {};
};

class SpriteInfo
{
public:
    virtual ~SpriteInfo() = default;
    virtual auto FillData(RenderDrawBuffer* dbuf, const FRect& pos, const tuple<uint, uint>& colors) const -> size_t = 0;

    int Width {};
    int Height {};
    int OffsX {};
    int OffsY {};
    TextureAtlas* Atlas {};
    RenderEffect* DrawEffect {};
};

class AtlasSprite : public SpriteInfo
{
public:
    auto FillData(RenderDrawBuffer* dbuf, const FRect& pos, const tuple<uint, uint>& colors) const -> size_t override;

    AtlasType DataAtlasType {};
    bool DataAtlasOneImage {};
    FRect AtlasRect {};
    vector<bool> HitTestData {};
};

class ParticleSprite : public AtlasSprite
{
public:
    ParticleSystem* Particle {};
};

#if FO_ENABLE_3D
class ModelSprite : public AtlasSprite
{
public:
    ModelInstance* Model {};
};
#endif

struct AnyFrames
{
    [[nodiscard]] auto GetSprId(uint num_frm = 0) const -> uint;
    [[nodiscard]] auto GetCurSprId(time_point time) const -> uint;
    [[nodiscard]] auto GetCurSprIndex(time_point time) const -> uint;
    [[nodiscard]] auto GetDir(uint dir) -> AnyFrames*;

    uint Ind[MAX_FRAMES] {}; // Sprite Ids
    int NextX[MAX_FRAMES] {};
    int NextY[MAX_FRAMES] {};
    uint CntFrm {};
    uint Ticks {}; // Time of playing animation
    uint Anim1 {};
    uint Anim2 {};
    hstring Name {};
    uint DirCount {1};
    AnyFrames* Dirs[7] {}; // 7 additional for square hexes, 5 for hexagonal
};

struct PrimitivePoint
{
    int PointX {};
    int PointY {};
    uint PointColor {};
    int* PointOffsX {};
    int* PointOffsY {};
};
static_assert(std::is_standard_layout_v<PrimitivePoint>);

struct DipData
{
    RenderTexture* MainTex {};
    RenderEffect* SourceEffect {};
    size_t IndCount {};
};

class SpriteManager final
{
public:
    SpriteManager() = delete;
    SpriteManager(RenderSettings& settings, AppWindow* window, FileSystem& resources, EffectManager& effect_mngr);
    SpriteManager(const SpriteManager&) = delete;
    SpriteManager(SpriteManager&&) noexcept = delete;
    auto operator=(const SpriteManager&) = delete;
    auto operator=(SpriteManager&&) noexcept = delete;
    ~SpriteManager();

    [[nodiscard]] auto GetWindow() { NON_CONST_METHOD_HINT_ONELINE() return _window; }
    [[nodiscard]] auto GetWindowSize() const -> tuple<int, int>;
    [[nodiscard]] auto GetScreenSize() const -> tuple<int, int>;
    [[nodiscard]] auto IsWindowFocused() const -> bool;
    [[nodiscard]] auto CreateRenderTarget(bool with_depth, RenderTarget::SizeType size, int width, int height, bool linear_filtered) -> RenderTarget*;
    [[nodiscard]] auto GetRenderTargetPixel(RenderTarget* rt, int x, int y) const -> uint;
    [[nodiscard]] auto GetSpriteInfo(uint id) const -> const SpriteInfo* { return _sprData[id]; }
    [[nodiscard]] auto GetSpriteInfoForEditing(uint id) -> SpriteInfo* { NON_CONST_METHOD_HINT_ONELINE() return _sprData[id]; }
    [[nodiscard]] auto GetDrawRect(const MapSprite* spr) const -> IRect;
    [[nodiscard]] auto GetViewRect(const MapSprite* spr) const -> IRect;
    [[nodiscard]] auto IsPixNoTransp(uint spr_id, int offs_x, int offs_y, bool with_zoom) const -> bool;
    [[nodiscard]] auto IsEggTransp(int pix_x, int pix_y) const -> bool;
    [[nodiscard]] auto CheckEggAppearence(uint16 hx, uint16 hy, EggAppearenceType egg_appearence) const -> bool;
    [[nodiscard]] auto IsAccumulateAtlasActive() const -> bool;
    [[nodiscard]] auto LoadAnimation(string_view fname, bool use_dummy) -> AnyFrames*;
    [[nodiscard]] auto ReloadAnimation(AnyFrames* anim, string_view fname) -> AnyFrames*;
    [[nodiscard]] auto CreateAnyFrames(uint frames, uint ticks) -> AnyFrames*;
    [[nodiscard]] auto LoadParticle(string_view name, bool auto_draw_to_atlas) -> unique_del_ptr<ParticleSystem>;
    [[nodiscard]] auto GetParticleSprId(const ParticleSystem* particle) const -> uint;
#if FO_ENABLE_3D
    [[nodiscard]] auto LoadModel(string_view fname, bool auto_draw_to_atlas) -> unique_del_ptr<ModelInstance>;
    [[nodiscard]] auto GetModelSprId(const ModelInstance* model) const -> uint;
#endif

    void SetWindowSize(int w, int h);
    void SetScreenSize(int w, int h);
    void SwitchFullscreen();
    void SetMousePosition(int x, int y);
    void MinimizeWindow();
    auto EnableFullscreen() -> bool;
    auto DisableFullscreen() -> bool;
    void BlinkWindow();
    void SetAlwaysOnTop(bool enable);
    void BeginScene(uint clear_color);
    void EndScene();
    void PushRenderTarget(RenderTarget* rt);
    void PopRenderTarget();
    void DrawRenderTarget(const RenderTarget* rt, bool alpha_blend, const IRect* region_from = nullptr, const IRect* region_to = nullptr);
    void DrawTexture(const RenderTexture* tex, bool alpha_blend, const IRect* region_from = nullptr, const IRect* region_to = nullptr, RenderEffect* custom_effect = nullptr);
    void ClearCurrentRenderTarget(uint color, bool with_depth = false);
    void DeleteRenderTarget(RenderTarget* rt);
    void PushAtlasType(AtlasType atlas_type);
    void PushAtlasType(AtlasType atlas_type, bool one_image);
    void PopAtlasType();
    void AccumulateAtlasData();
    void FlushAccumulatedAtlasData();
    void DestroyAtlases(AtlasType atlas_type);
    void DumpAtlases() const;
    void CreateAnyFramesDirAnims(AnyFrames* anim, uint dirs);
    void DestroyAnyFrames(AnyFrames* anim);
    void PrepareSquare(vector<PrimitivePoint>& points, const IRect& r, uint color);
    void PrepareSquare(vector<PrimitivePoint>& points, IPoint lt, IPoint rt, IPoint lb, IPoint rb, uint color);
    void PushScissor(int l, int t, int r, int b);
    void PopScissor();
    void SetSpritesZoom(float zoom) noexcept;
    void Flush();
    void DrawSprite(uint id, int x, int y, uint color);
    void DrawSpriteSize(uint id, int x, int y, int w, int h, bool zoom_up, bool center, uint color);
    void DrawSpriteSizeExt(uint id, int x, int y, int w, int h, bool zoom_up, bool center, bool stretch, uint color);
    void DrawSpritePattern(uint id, int x, int y, int w, int h, int spr_width, int spr_height, uint color);
    void DrawSprites(MapSpriteList& list, bool collect_contours, bool use_egg, DrawOrderType draw_oder_from, DrawOrderType draw_oder_to, uint color);
    void DrawPoints(const vector<PrimitivePoint>& points, RenderPrimitiveType prim, const float* zoom = nullptr, const FPoint* offset = nullptr, RenderEffect* custom_effect = nullptr);

    void DrawContours();
    void InitializeEgg(string_view egg_name);
    void SetEgg(uint16 hx, uint16 hy, const MapSprite* spr);
    void EggNotValid() { _eggValid = false; }

    void InitParticleSubsystem(GameTimer& game_time);
    void DrawParticleToAtlas(ParticleSystem* particle);

#if FO_ENABLE_3D
    void Init3dSubsystem(GameTimer& game_time, NameResolver& name_resolver, AnimationResolver& anim_name_resolver);
    void Preload3dModel(string_view model_name);
    void DrawModelToAtlas(ModelInstance* model);
    void DrawModel(int x, int y, ModelInstance* model, uint color);
#endif

private:
    void AllocateRenderTargetTexture(RenderTarget* rt, bool linear_filtered, bool with_depth);

    auto CreateAtlas(int request_width, int request_height) -> TextureAtlas*;
    auto FindAtlasPlace(const AtlasSprite* si, int& x, int& y) -> TextureAtlas*;
    auto RequestFillAtlas(AtlasSprite* si, int width, int height, const uint* data) -> uint;
    void FillAtlas(AtlasSprite* si, const uint* data);

    void RefreshScissor();
    void EnableScissor();
    void DisableScissor();

    void CollectContour(int x, int y, const SpriteInfo* si, uint contour_color);

    auto Load2dAnimation(string_view fname) -> AnyFrames*;
#if FO_ENABLE_3D
    auto Load3dAnimation(string_view fname) -> AnyFrames*;
#endif

    auto LoadTexture(string_view path, unordered_map<string, const AtlasSprite*>& collection, AtlasType atlas) -> pair<RenderTexture*, FRect>;

    void AddParticleToAtlas(ParticleSystem* particle);
#if FO_ENABLE_3D
    void AddModelToAtlas(ModelInstance* model);
#endif

    void OnScreenSizeChanged();

    RenderSettings& _settings;
    AppWindow* _window;
    FileSystem& _resources;
    EffectManager& _effectMngr;
    EventUnsubscriber _eventUnsubscriber {};

    AnyFrames* _dummyAnim {};

    RenderTarget* _rtMain {};
    RenderTarget* _rtContours {};
    RenderTarget* _rtContoursMid {};
    vector<RenderTarget*> _rtIntermediate {};
    vector<RenderTarget*> _rtStack {};
    vector<unique_ptr<RenderTarget>> _rtAll {};

    vector<tuple<AtlasType, bool>> _targetAtlasStack {};
    vector<unique_ptr<TextureAtlas>> _allAtlases {};

    bool _accumulatorActive {};
    vector<pair<AtlasSprite*, uint*>> _accumulatorSprInfo {};

    vector<SpriteInfo*> _sprData {};

    MemoryPool<AnyFrames, ANY_FRAMES_POOL_SIZE> _anyFramesPool {};

    vector<DipData> _dipQueue {};
    RenderDrawBuffer* _spritesDrawBuf {};
    RenderDrawBuffer* _primitiveDrawBuf {};
    RenderDrawBuffer* _flushDrawBuf {};
    RenderDrawBuffer* _contourDrawBuf {};
    size_t _flushVertCount {};

    vector<int> _scissorStack {};
    IRect _scissorRect {};

    bool _contoursAdded {};
    bool _contourClearMid {};

    bool _eggValid {};
    uint16 _eggHx {};
    uint16 _eggHy {};
    int _eggX {};
    int _eggY {};
    const AtlasSprite* _sprEgg {};
    vector<uint> _eggData {};

    vector<uint> _borderBuf {};

    float _spritesZoom {1.0f};

    int _windowSizeDiffX {};
    int _windowSizeDiffY {};

    unique_ptr<ParticleManager> _particleMngr {};
    unordered_map<string, const AtlasSprite*> _loadedParticleTextures {};
    vector<ParticleSystem*> _autoDrawParticles {};
    unordered_map<const ParticleSystem*, tuple<uint, AtlasType>> _particlesInfo {};

#if FO_ENABLE_3D
    unique_ptr<ModelManager> _modelMngr {};
    unordered_map<string, const AtlasSprite*> _loadedMeshTextures {};
    vector<ModelInstance*> _autoDrawModels {};
    unordered_map<const ModelInstance*, tuple<uint, AtlasType>> _modelsInfo {};
#endif

    bool _nonConstHelper {};

    // Todo: move fonts stuff to separate module
public:
    [[nodiscard]] auto GetLinesCount(int width, int height, string_view str, int num_font) -> int;
    [[nodiscard]] auto GetLinesHeight(int width, int height, string_view str, int num_font) -> int;
    [[nodiscard]] auto GetLineHeight(int num_font) -> int;
    [[nodiscard]] auto GetTextInfo(int width, int height, string_view str, int num_font, uint flags, int& tw, int& th, int& lines) -> bool;
    [[nodiscard]] auto HaveLetter(int num_font, uint letter) -> bool;

    auto LoadFontFO(int index, string_view font_name, bool not_bordered, bool skip_if_loaded) -> bool;
    auto LoadFontBmf(int index, string_view font_name) -> bool;
    void SetDefaultFont(int index, uint color);
    void SetFontEffect(int index, RenderEffect* effect);
    void BuildFonts();
    void DrawStr(const IRect& r, string_view str, uint flags, uint color, int num_font);
    auto SplitLines(const IRect& r, string_view cstr, int num_font) -> vector<string>;
    void ClearFonts();

private:
    static constexpr int FONT_BUF_LEN = 0x5000;
    static constexpr int FONT_MAX_LINES = 1000;
    static constexpr int FORMAT_TYPE_DRAW = 0;
    static constexpr int FORMAT_TYPE_SPLIT = 1;
    static constexpr int FORMAT_TYPE_LCOUNT = 2;

    struct FontData
    {
        struct Letter
        {
            int16 PosX {};
            int16 PosY {};
            int16 Width {};
            int16 Height {};
            int16 OffsX {};
            int16 OffsY {};
            int16 XAdvance {};
            FRect TexUV {};
            FRect TexBorderedUV {};
        };

        RenderEffect* DrawEffect {};
        bool Builded {};
        RenderTexture* FontTex {};
        RenderTexture* FontTexBordered {};
        map<uint, Letter> Letters {};
        int SpaceWidth {};
        int LineHeight {};
        int YAdvance {};
        AnyFrames* ImageNormal {};
        AnyFrames* ImageBordered {};
        bool MakeGray {};
    };

    // Todo: optimize text formatting - cache previous results
    struct FontFormatInfo
    {
        FontData* CurFont {};
        uint Flags {};
        IRect Region {};
        char Str[FONT_BUF_LEN] {};
        char* PStr {};
        int LinesAll {1};
        int LinesInRect {};
        int CurX {};
        int CurY {};
        int MaxCurX {};
        uint ColorDots[FONT_BUF_LEN] {};
        int LineWidth[FONT_MAX_LINES] {};
        int LineSpaceWidth[FONT_MAX_LINES] {};
        int OffsColDots {};
        uint DefColor {COLOR_TEXT};
        vector<string>* StrLines {};
        bool IsError {};
    };

    [[nodiscard]] auto GetFont(int num) -> FontData*;

    void BuildFont(int index);
    void FormatText(FontFormatInfo& fi, int fmt_type);

    vector<unique_ptr<FontData>> _allFonts {};
    int _defFontIndex {-1};
    uint _defFontColor {};
    FontFormatInfo _fontFormatInfoBuf {};
};
