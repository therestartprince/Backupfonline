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

#include "ProtoManager.h"
#include "FileSystem.h"
#include "GenericUtils.h"
#include "Log.h"
#include "StringUtils.h"

template<class T>
static void WriteProtosToBinary(vector<uchar>& data, const map<hstring, T*>& protos)
{
    WriteData(data, static_cast<uint>(protos.size()));
    for (auto& kv : protos) {
        auto* proto_item = kv.second;

        const auto proto_id = kv.first;
        WriteData(data, proto_id);

        const auto proto_name = proto_item->GetName();
        WriteData(data, static_cast<ushort>(proto_name.length()));
        WriteDataArr(data, proto_name.data(), proto_name.length());

        WriteData(data, static_cast<ushort>(proto_item->GetComponents().size()));
        for (auto component : proto_item->GetComponents()) {
            const auto component_str = component.as_str();
            WriteData(data, static_cast<ushort>(component_str.length()));
            WriteDataArr(data, component_str.data(), component_str.length());
        }

        vector<uchar*>* props_data = nullptr;
        vector<uint>* props_data_sizes = nullptr;
        proto_item->StoreData(true, &props_data, &props_data_sizes);

        WriteData(data, static_cast<ushort>(props_data->size()));
        for (size_t i = 0; i < props_data->size(); i++) {
            const auto cur_size = props_data_sizes->at(i);
            WriteData(data, cur_size);
            WriteDataArr(data, props_data->at(i), cur_size);
        }
    }
}

template<class T>
static void ReadProtosFromBinary(NameResolver& name_resolver, const PropertyRegistrator* property_registrator, const vector<uchar>& data, uint& pos, map<hstring, T*>& protos)
{
    vector<const uchar*> props_data;
    vector<uint> props_data_sizes;
    const auto protos_count = ReadData<uint>(data, pos);
    for (uint i = 0; i < protos_count; i++) {
        const auto proto_name_len = ReadData<ushort>(data, pos);
        const auto proto_name = string(ReadDataArr<char>(data, proto_name_len, pos), proto_name_len);
        const auto proto_id = name_resolver.ToHashedString(proto_name);

        auto* proto = new std::remove_const_t<T>(proto_id, property_registrator);

        const auto components_count = ReadData<ushort>(data, pos);
        for (ushort j = 0; j < components_count; j++) {
            const auto component_name_len = ReadData<ushort>(data, pos);
            const auto component_name = string(ReadDataArr<char>(data, component_name_len, pos), component_name_len);
            const auto component_name_hashed = name_resolver.ToHashedString(component_name);
            proto->GetComponents().insert(component_name_hashed);
        }

        const uint data_count = ReadData<ushort>(data, pos);
        props_data.resize(data_count);
        props_data_sizes.resize(data_count);
        for (uint j = 0; j < data_count; j++) {
            props_data_sizes[j] = ReadData<uint>(data, pos);
            const auto* const_props_data = ReadDataArr<uchar>(data, props_data_sizes[j], pos);
            props_data[j] = const_cast<uchar*>(const_props_data);
        }
        proto->RestoreData(props_data, props_data_sizes);
        RUNTIME_ASSERT(!protos.count(proto_id));
        protos.insert(std::make_pair(proto_id, proto));
    }
}

static void InsertMapValues(const map<string, string>& from_kv, map<string, string>& to_kv, bool overwrite)
{
    for (const auto& [key, value] : from_kv) {
        RUNTIME_ASSERT(!key.empty());

        if (key[0] != '$') {
            if (overwrite) {
                to_kv[key] = value;
            }
            else {
                to_kv.insert(std::make_pair(key, value));
            }
        }
        else if (key == "$Components" && !value.empty()) {
            if (to_kv.count("$Components") == 0u) {
                to_kv["$Components"] = value;
            }
            else {
                to_kv["$Components"] += " " + value;
            }
        }
    }
}

template<class T>
static void ParseProtos(FileManager& file_mngr, NameResolver& name_resolver, const PropertyRegistrator* property_registrator, string_view ext, string_view app_name, map<hstring, T*>& protos)
{
    // Collect data
    auto files = file_mngr.FilterFiles(ext);
    map<hstring, map<string, string>> files_protos;
    map<hstring, map<string, map<string, string>>> files_texts;
    while (files.MoveNext()) {
        auto file = files.GetCurFile();
        ConfigFile fopro(file.GetCStr(), name_resolver);

        auto protos_data = fopro.GetApps(app_name);
        if (std::is_same_v<T, ProtoMap> && protos_data.empty()) {
            protos_data = fopro.GetApps("Header");
        }

        for (auto& pkv : protos_data) {
            auto& kv = *pkv;
            auto name = kv.count("$Name") ? kv["$Name"] : file.GetName();
            auto pid = name_resolver.ToHashedString(name);
            if (files_protos.count(pid)) {
                throw ProtoManagerException("Proto already loaded", name);
            }

            files_protos.insert(std::make_pair(pid, kv));

            for (const auto& app : fopro.GetAppNames()) {
                if (app.size() == "Text_xxxx"_len && _str(app).startsWith("Text_")) {
                    if (!files_texts.count(pid)) {
                        map<string, map<string, string>> texts;
                        files_texts.insert(std::make_pair(pid, texts));
                    }
                    files_texts[pid].insert(std::make_pair(app, fopro.GetApp(app)));
                }
            }
        }

        if (protos_data.empty()) {
            throw ProtoManagerException("File does not contain any proto", file.GetName());
        }
    }

    // Injection
    auto injection = [&files_protos, &name_resolver](const char* key_name, bool overwrite) {
        for (auto& [pid, kv] : files_protos) {
            if (kv.count(key_name)) {
                for (const auto& inject_name : _str(kv[key_name]).split(' ')) {
                    if (inject_name == "All") {
                        for (auto& [pid2, kv2] : files_protos) {
                            if (pid2 != pid) {
                                InsertMapValues(kv, kv2, overwrite);
                            }
                        }
                    }
                    else {
                        auto inject_name_hashed = name_resolver.ToHashedString(inject_name);
                        if (!files_protos.count(inject_name_hashed)) {
                            throw ProtoManagerException("Proto not found for injection from another proto", inject_name, pid);
                        }
                        InsertMapValues(kv, files_protos[inject_name_hashed], overwrite);
                    }
                }
            }
        }
    };
    injection("$Inject", false);

    // Protos
    for (auto& [fst, snd] : files_protos) {
        const auto pid = fst;
        auto base_name = pid.as_str();
        RUNTIME_ASSERT(protos.count(pid) == 0);

        // Fill content from parents
        map<string, string> final_kv;
        std::function<void(string_view, map<string, string>&)> fill_parent = [&fill_parent, &base_name, &files_protos, &final_kv, &name_resolver](string_view name, map<string, string>& cur_kv) {
            const auto parent_name_line = cur_kv.count("$Parent") ? cur_kv["$Parent"] : string();
            for (auto& parent_name : _str(parent_name_line).split(' ')) {
                const auto parent_pid = name_resolver.ToHashedString(parent_name);
                auto parent = files_protos.find(parent_pid);
                if (parent == files_protos.end()) {
                    if (base_name == name) {
                        throw ProtoManagerException("Proto fail to load parent", base_name, parent_name);
                    }

                    throw ProtoManagerException("Proto fail to load parent for another proto", base_name, parent_name, name);
                }

                fill_parent(parent_name, parent->second);
                InsertMapValues(parent->second, final_kv, true);
            }
        };
        fill_parent(base_name, snd);

        // Actual content
        InsertMapValues(snd, final_kv, true);

        // Final injection
        injection("$InjectOverride", true);

        // Create proto
        auto* proto = new std::remove_const_t<T>(pid, property_registrator);
        if (!proto->LoadFromText(final_kv)) {
            delete proto;
            throw ProtoManagerException("Proto item fail to load properties", base_name);
        }

        // Components
        if (final_kv.count("$Components")) {
            for (const auto& component_name : _str(final_kv["$Components"]).split(' ')) {
                const auto component_name_hashed = name_resolver.ToHashedString(component_name);
                if (!proto->GetProperties().GetRegistrator()->IsComponentRegistered(component_name_hashed)) {
                    throw ProtoManagerException("Proto item has invalid component", base_name, component_name);
                }
                proto->GetComponents().insert(component_name_hashed);
            }
        }

        // Add to collection
        protos.insert(std::make_pair(pid, proto));
    }

    // Texts
    for (auto [pid, file_text] : files_texts) {
        auto* proto = const_cast<std::remove_const_t<T>*>(protos[pid]);
        RUNTIME_ASSERT(proto);

        for (auto [lang, pairs] : file_text) {
            FOMsg temp_msg;
            temp_msg.LoadFromMap(pairs);

            auto* msg = new FOMsg();
            uint str_num = 0;
            while ((str_num = temp_msg.GetStrNumUpper(str_num))) {
                const auto count = temp_msg.Count(str_num);
                auto new_str_num = str_num;

                if constexpr (std::is_same_v<T, ProtoItem>) {
                    new_str_num = ITEM_STR_ID(proto->ProtoId, str_num);
                }
                else if constexpr (std::is_same_v<T, ProtoCritter>) {
                    new_str_num = CR_STR_ID(proto->ProtoId, str_num);
                }
                else if constexpr (std::is_same_v<T, ProtoLocation>) {
                    new_str_num = LOC_STR_ID(proto->ProtoId, str_num);
                }

                for (const auto n : xrange(count)) {
                    msg->AddStr(new_str_num, temp_msg.GetStr(str_num, n));
                }
            }

            proto->TextsLang.push_back(*reinterpret_cast<const uint*>(lang.substr("Text_"_len).c_str()));
            proto->Texts.push_back(msg);
        }
    }
}

ProtoManager::ProtoManager(FileManager& file_mngr, FOEngineBase& engine) : _nameResolver {engine}
{
    ParseProtos(file_mngr, _nameResolver, engine.GetPropertyRegistrator(ItemProperties::ENTITY_CLASS_NAME), "foitem", "ProtoItem", _itemProtos);
    ParseProtos(file_mngr, _nameResolver, engine.GetPropertyRegistrator(CritterProperties::ENTITY_CLASS_NAME), "focr", "ProtoCritter", _crProtos);
    ParseProtos(file_mngr, _nameResolver, engine.GetPropertyRegistrator(MapProperties::ENTITY_CLASS_NAME), "fomap", "ProtoMap", _mapProtos);
    ParseProtos(file_mngr, _nameResolver, engine.GetPropertyRegistrator(LocationProperties::ENTITY_CLASS_NAME), "foloc", "ProtoLocation", _locProtos);

    // Mapper collections
    for (auto [pid, proto] : _itemProtos) {
        if (!proto->GetComponents().empty()) {
            const_cast<ProtoItem*>(proto)->CollectionName = _str(*proto->GetComponents().begin()).lower();
        }
        else {
            const_cast<ProtoItem*>(proto)->CollectionName = "other";
        }
    }

    for (auto [pid, proto] : _crProtos) {
        const_cast<ProtoCritter*>(proto)->CollectionName = "all";
    }

    // Check player proto
    if (_crProtos.count(_nameResolver.ToHashedString("Player")) == 0u) {
        throw ProtoManagerException("Player proto 'Player.focr' not loaded");
    }

    // Check maps for locations
    for (auto [pid, proto] : _locProtos) {
        for (auto map_pid : proto->GetMapProtos()) {
            if (_mapProtos.count(map_pid) == 0u) {
                throw ProtoManagerException("Proto map not found for proto location", map_pid, proto->GetName());
            }
        }
    }
}

ProtoManager::ProtoManager(const vector<uchar>& data, FOEngineBase& engine) : _nameResolver {engine}
{
    if (data.empty()) {
        return;
    }

    const auto uncompressed_data = Compressor::Uncompress(data, 15);
    if (uncompressed_data.empty()) {
        throw ProtoManagerException("Unable to uncompress data");
    }

    uint pos = 0;
    ReadProtosFromBinary(_nameResolver, engine.GetPropertyRegistrator(ItemProperties::ENTITY_CLASS_NAME), uncompressed_data, pos, _itemProtos);
    ReadProtosFromBinary(_nameResolver, engine.GetPropertyRegistrator(CritterProperties::ENTITY_CLASS_NAME), uncompressed_data, pos, _crProtos);
    ReadProtosFromBinary(_nameResolver, engine.GetPropertyRegistrator(MapProperties::ENTITY_CLASS_NAME), uncompressed_data, pos, _mapProtos);
    ReadProtosFromBinary(_nameResolver, engine.GetPropertyRegistrator(LocationProperties::ENTITY_CLASS_NAME), uncompressed_data, pos, _locProtos);
}

auto ProtoManager::GetProtosBinaryData() const -> vector<uchar>
{
    vector<uchar> data;
    WriteProtosToBinary(data, _itemProtos);
    WriteProtosToBinary(data, _crProtos);
    WriteProtosToBinary(data, _mapProtos);
    WriteProtosToBinary(data, _locProtos);
    return Compressor::Compress(data);
}

template<typename T>
static auto ValidateProtoResourcesExt(NameResolver& name_resolver, const map<hstring, T*>& protos, set<hstring>& hashes) -> int
{
    auto errors = 0;
    for (auto& kv : protos) {
        T* proto = kv.second;
        const auto* registrator = proto->GetProperties().GetRegistrator();
        for (uint i = 0; i < registrator->GetCount(); i++) {
            auto* prop = registrator->GetByIndex(i);
            if (prop->IsBaseTypeResource()) {
                const auto h = proto->GetProperties().template GetValue<hstring>(prop);
                if (h && !hashes.count(h)) {
                    WriteLog("Resource '{}' not found for property '{}' in prototype '{}'.\n", h, prop->GetName(), proto->GetName());
                    errors++;
                }
            }
        }
    }
    return errors;
}

auto ProtoManager::ValidateProtoResources(const vector<string>& resource_names) const -> bool
{
    set<hstring> hashes;
    for (const auto& name : resource_names) {
        hashes.insert(_nameResolver.ToHashedString(name));
    }

    auto errors = 0;
    errors += ValidateProtoResourcesExt(_nameResolver, _itemProtos, hashes);
    errors += ValidateProtoResourcesExt(_nameResolver, _crProtos, hashes);
    errors += ValidateProtoResourcesExt(_nameResolver, _mapProtos, hashes);
    errors += ValidateProtoResourcesExt(_nameResolver, _locProtos, hashes);
    return errors == 0;
}

auto ProtoManager::GetProtoItem(hstring proto_id) -> const ProtoItem*
{
    const auto it = _itemProtos.find(proto_id);
    return it != _itemProtos.end() ? it->second : nullptr;
}

auto ProtoManager::GetProtoCritter(hstring proto_id) -> const ProtoCritter*
{
    const auto it = _crProtos.find(proto_id);
    return it != _crProtos.end() ? it->second : nullptr;
}

auto ProtoManager::GetProtoMap(hstring proto_id) -> const ProtoMap*
{
    const auto it = _mapProtos.find(proto_id);
    return it != _mapProtos.end() ? it->second : nullptr;
}

auto ProtoManager::GetProtoLocation(hstring proto_id) -> const ProtoLocation*
{
    const auto it = _locProtos.find(proto_id);
    return it != _locProtos.end() ? it->second : nullptr;
}

auto ProtoManager::GetProtoItems() const -> const map<hstring, const ProtoItem*>&
{
    return _itemProtos;
}

auto ProtoManager::GetProtoCritters() const -> const map<hstring, const ProtoCritter*>&
{
    return _crProtos;
}

auto ProtoManager::GetProtoMaps() const -> const map<hstring, const ProtoMap*>&
{
    return _mapProtos;
}

auto ProtoManager::GetProtoLocations() const -> const map<hstring, const ProtoLocation*>&
{
    return _locProtos;
}
