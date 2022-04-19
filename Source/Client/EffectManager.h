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

#pragma once

#include "Common.h"

#include "Application.h"
#include "FileSystem.h"
#include "Settings.h"
#include "Timer.h"

DECLARE_EXCEPTION(EffectManagerException);

class FOServer;

struct EffectCollection
{
    RenderEffect* Contour {};
    RenderEffect* ContourDefault {};
    RenderEffect* Generic {};
    RenderEffect* GenericDefault {};
    RenderEffect* Critter {};
    RenderEffect* CritterDefault {};
    RenderEffect* Tile {};
    RenderEffect* TileDefault {};
    RenderEffect* Roof {};
    RenderEffect* RoofDefault {};
    RenderEffect* Rain {};
    RenderEffect* RainDefault {};
    RenderEffect* Iface {};
    RenderEffect* IfaceDefault {};
    RenderEffect* Primitive {};
    RenderEffect* PrimitiveDefault {};
    RenderEffect* Light {};
    RenderEffect* LightDefault {};
    RenderEffect* Fog {};
    RenderEffect* FogDefault {};
    RenderEffect* FlushRenderTarget {};
    RenderEffect* FlushRenderTargetDefault {};
    RenderEffect* FlushPrimitive {};
    RenderEffect* FlushPrimitiveDefault {};
    RenderEffect* FlushMap {};
    RenderEffect* FlushMapDefault {};
    RenderEffect* FlushLight {};
    RenderEffect* FlushLightDefault {};
    RenderEffect* FlushFog {};
    RenderEffect* FlushFogDefault {};
    RenderEffect* Font {};
    RenderEffect* FontDefault {};
    RenderEffect* Skinned3d {};
    RenderEffect* Skinned3dDefault {};
};

class EffectManager final
{
public:
    EffectManager(RenderSettings& settings, FileManager& file_mngr, GameTimer& game_time);
    EffectManager(const EffectManager&) = delete;
    EffectManager(EffectManager&&) = delete;
    auto operator=(const EffectManager&) -> EffectManager& = delete;
    auto operator=(EffectManager&&) -> EffectManager& = delete;
    ~EffectManager() = default;

    [[nodiscard]] auto LoadEffect(string_view name, string_view defines, string_view base_path) -> RenderEffect*;

    void LoadMinimalEffects();
    void LoadDefaultEffects();
    void Load3dEffects();

    EffectCollection Effects {};

private:
    void PerFrameEffectUpdate(RenderEffect* effect) const;

    RenderSettings& _settings;
    FileManager& _fileMngr;
    GameTimer& _gameTime;
    vector<unique_ptr<RenderEffect>> _loadedEffects {};
    EventUnsubscriber _eventUnsubscriber {};
};
