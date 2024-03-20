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
// Copyright (c) 2006 - 2023, Anton Tsvetinskiy aka cvet <cvet@tut.by>
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

#include "Entity.h"
#include "Application.h"
#include "Log.h"

Entity::Entity(const PropertyRegistrator* registrator, const Properties* props) :
    _props {registrator}
{
    STACK_TRACE_ENTRY();

    _props.SetEntity(this);

    if (props != nullptr) {
        _props = *props;
    }
}

void Entity::AddRef() const noexcept
{
    NO_STACK_TRACE_ENTRY();

    ++_refCounter;
}

void Entity::Release() const noexcept
{
    NO_STACK_TRACE_ENTRY();

    if (--_refCounter == 0) {
        delete this;
    }
}

auto Entity::GetTypeName() const -> hstring
{
    NO_STACK_TRACE_ENTRY();

    return _props.GetRegistrator()->GetTypeName();
}

auto Entity::GetTypeNamePlural() const -> hstring
{
    NO_STACK_TRACE_ENTRY();

    return _props.GetRegistrator()->GetTypeNamePlural();
}

auto Entity::GetProperties() const -> const Properties&
{
    NO_STACK_TRACE_ENTRY();

    return _props;
}

auto Entity::GetPropertiesForEdit() -> Properties&
{
    NO_STACK_TRACE_ENTRY();

    return _props;
}

auto Entity::GetEventCallbacks(const string& event_name) -> vector<EventCallbackData>*
{
    STACK_TRACE_ENTRY();

    if (const auto it = _events.find(event_name); it != _events.end()) {
        return &it->second;
    }

    return &_events.emplace(event_name, vector<EventCallbackData>()).first->second;
}

void Entity::SubscribeEvent(const string& event_name, EventCallbackData&& callback)
{
    STACK_TRACE_ENTRY();

    SubscribeEvent(GetEventCallbacks(event_name), std::move(callback));
}

void Entity::UnsubscribeEvent(const string& event_name, const void* subscription_ptr)
{
    STACK_TRACE_ENTRY();

    if (const auto it = _events.find(event_name); it != _events.end()) {
        UnsubscribeEvent(&it->second, subscription_ptr);
    }
}

void Entity::UnsubscribeAllEvent(const string& event_name)
{
    STACK_TRACE_ENTRY();

    if (const auto it = _events.find(event_name); it != _events.end()) {
        it->second.clear();
    }
}

auto Entity::FireEvent(const string& event_name, const initializer_list<void*>& args) -> bool
{
    STACK_TRACE_ENTRY();

    if (const auto it = _events.find(event_name); it != _events.end()) {
        return FireEvent(&it->second, args);
    }
    return true;
}

void Entity::SubscribeEvent(vector<EventCallbackData>* callbacks, EventCallbackData&& callback)
{
    STACK_TRACE_ENTRY();

    NON_CONST_METHOD_HINT();

    RUNTIME_ASSERT(callbacks);

    if (callback.Priority >= EventPriority::Highest && std::find_if(callbacks->begin(), callbacks->end(), [](const EventCallbackData& cb) { return cb.Priority >= EventPriority::Highest; }) != callbacks->end()) {
        throw GenericException("Highest callback already added");
    }

    if (callback.Priority <= EventPriority::Lowest && std::find_if(callbacks->begin(), callbacks->end(), [](const EventCallbackData& cb) { return cb.Priority <= EventPriority::Lowest; }) != callbacks->end()) {
        throw GenericException("Lowest callback already added");
    }

    callbacks->push_back(std::move(callback));

    std::stable_sort(callbacks->begin(), callbacks->end(), [](const EventCallbackData& cb1, const EventCallbackData& cb2) {
        // From highest to lowest
        return cb1.Priority > cb2.Priority;
    });
}

void Entity::UnsubscribeEvent(vector<EventCallbackData>* callbacks, const void* subscription_ptr)
{
    STACK_TRACE_ENTRY();

    NON_CONST_METHOD_HINT();

    RUNTIME_ASSERT(callbacks);

    if (const auto it = std::find_if(callbacks->begin(), callbacks->end(), [subscription_ptr](const auto& cb) { return cb.SubscribtionPtr == subscription_ptr; }); it != callbacks->end()) {
        callbacks->erase(it);
    }
}

// Param callbacks mutable beacuse callbacks may change it, so make it explicit
// ReSharper disable once CppParameterMayBeConstPtrOrRef
auto Entity::FireEvent(vector<EventCallbackData>* callbacks, const initializer_list<void*>& args) -> bool
{
    STACK_TRACE_ENTRY();

    RUNTIME_ASSERT(callbacks);

    if (callbacks->empty()) {
        return true;
    }

    for (const auto& cb : copy(*callbacks)) {
        const auto ex_policy = cb.ExPolicy;

        try {
            if (!cb.Callback(args)) {
                return false;
            }
        }
        catch (const std::exception& ex) {
            if (ex_policy == EventExceptionPolicy::PropogateException) {
                throw;
            }

            ReportExceptionAndContinue(ex);

            if (ex_policy == EventExceptionPolicy::StopChainAndReturnTrue) {
                return true;
            }
            if (ex_policy == EventExceptionPolicy::StopChainAndReturnFalse) {
                return false;
            }
        }
    }

    return true;
}

void Entity::MarkAsDestroying()
{
    STACK_TRACE_ENTRY();

    RUNTIME_ASSERT(!_isDestroying);
    RUNTIME_ASSERT(!_isDestroyed);

    _isDestroying = true;
}

void Entity::MarkAsDestroyed()
{
    STACK_TRACE_ENTRY();

    RUNTIME_ASSERT(!_isDestroyed);

    _isDestroying = true;
    _isDestroyed = true;
}

void Entity::StoreData(bool with_protected, vector<const uint8*>** all_data, vector<uint>** all_data_sizes) const
{
    STACK_TRACE_ENTRY();

    _props.StoreData(with_protected, all_data, all_data_sizes);
}

void Entity::RestoreData(const vector<vector<uint8>>& props_data)
{
    STACK_TRACE_ENTRY();

    _props.RestoreData(props_data);
}

void Entity::SetValueFromData(const Property* prop, PropertyRawData& prop_data)
{
    STACK_TRACE_ENTRY();

    _props.SetValueFromData(prop, prop_data);
}

auto Entity::GetValueAsInt(const Property* prop) const -> int
{
    STACK_TRACE_ENTRY();

    return _props.GetPlainDataValueAsInt(prop);
}

auto Entity::GetValueAsInt(int prop_index) const -> int
{
    STACK_TRACE_ENTRY();

    return _props.GetValueAsInt(prop_index);
}

auto Entity::GetValueAsAny(const Property* prop) const -> any_t
{
    STACK_TRACE_ENTRY();

    return _props.GetPlainDataValueAsAny(prop);
}

auto Entity::GetValueAsAny(int prop_index) const -> any_t
{
    STACK_TRACE_ENTRY();

    return _props.GetValueAsAny(prop_index);
}

void Entity::SetValueAsInt(const Property* prop, int value)
{
    STACK_TRACE_ENTRY();

    _props.SetPlainDataValueAsInt(prop, value);
}

void Entity::SetValueAsInt(int prop_index, int value)
{
    STACK_TRACE_ENTRY();

    _props.SetValueAsInt(prop_index, value);
}

void Entity::SetValueAsAny(const Property* prop, const any_t& value)
{
    STACK_TRACE_ENTRY();

    _props.SetPlainDataValueAsAny(prop, value);
}

void Entity::SetValueAsAny(int prop_index, const any_t& value)
{
    STACK_TRACE_ENTRY();

    _props.SetValueAsAny(prop_index, value);
}

auto Entity::GetInnerEntities(hstring entry) -> const vector<Entity*>*
{
    STACK_TRACE_ENTRY();

    NON_CONST_METHOD_HINT();

    if (!_innerEntities) {
        return nullptr;
    }

    const auto it_entry = _innerEntities->find(entry);

    if (it_entry == _innerEntities->end()) {
        return nullptr;
    }

    return &it_entry->second;
}

void Entity::AddInnerEntity(hstring entry, Entity* entity)
{
    STACK_TRACE_ENTRY();

    if (_innerEntities == nullptr) {
        _innerEntities = std::make_unique<unordered_map<hstring, vector<Entity*>>>();
    }

    if (const auto it = _innerEntities->find(entry); it == _innerEntities->end()) {
        _innerEntities->emplace(entry, vector {entity});
    }
    else {
        it->second.emplace_back(entity);
    }
}

void Entity::RemoveInnerEntity(hstring entry, Entity* entity)
{
    STACK_TRACE_ENTRY();

    RUNTIME_ASSERT(_innerEntities);
    RUNTIME_ASSERT(entry);
    RUNTIME_ASSERT(_innerEntities->count(entry));

    auto& entities = _innerEntities->at(entry);

    const auto it = std::find(entities.begin(), entities.end(), entity);
    RUNTIME_ASSERT(it != entities.end());
    entities.erase(it);

    if (entities.empty()) {
        _innerEntities->erase(entry);

        if (_innerEntities->empty()) {
            _innerEntities.reset();
        }
    }
}

void Entity::ClearInnerEntities()
{
    STACK_TRACE_ENTRY();

    _innerEntities.reset();
}

ProtoEntity::ProtoEntity(hstring proto_id, const PropertyRegistrator* registrator, const Properties* props) :
    Entity(registrator, props),
    _protoId {proto_id}
{
    STACK_TRACE_ENTRY();

    RUNTIME_ASSERT(_protoId);
}

auto ProtoEntity::GetName() const -> string_view
{
    NO_STACK_TRACE_ENTRY();

    return _protoId.as_str();
}

auto ProtoEntity::GetProtoId() const -> hstring
{
    NO_STACK_TRACE_ENTRY();

    return _protoId;
}

void ProtoEntity::EnableComponent(hstring component)
{
    STACK_TRACE_ENTRY();

    _components.emplace(component);
    _componentHashes.emplace(component.as_hash());
}

auto ProtoEntity::HasComponent(hstring name) const -> bool
{
    NO_STACK_TRACE_ENTRY();

    return _components.count(name) != 0;
}

auto ProtoEntity::HasComponent(hstring::hash_t hash) const -> bool
{
    NO_STACK_TRACE_ENTRY();

    return _componentHashes.count(hash) != 0;
}

EntityWithProto::EntityWithProto(const ProtoEntity* proto) :
    _proto {proto}
{
    STACK_TRACE_ENTRY();

    RUNTIME_ASSERT(_proto);

    _proto->AddRef();
}

EntityWithProto::~EntityWithProto()
{
    STACK_TRACE_ENTRY();

    _proto->Release();
}

auto EntityWithProto::GetProtoId() const -> hstring
{
    NO_STACK_TRACE_ENTRY();

    return _proto->GetProtoId();
}

auto EntityWithProto::GetProto() const -> const ProtoEntity*
{
    NO_STACK_TRACE_ENTRY();

    return _proto;
}

EntityEventBase::EntityEventBase(Entity* entity, const char* callback_name) :
    _entity {entity},
    _callbackName {callback_name}
{
    STACK_TRACE_ENTRY();
}

void EntityEventBase::Subscribe(Entity::EventCallbackData&& callback)
{
    STACK_TRACE_ENTRY();

    if (_callbacks == nullptr) {
        _callbacks = _entity->GetEventCallbacks(_callbackName);
    }

    _entity->SubscribeEvent(_callbacks, std::move(callback));
}

// ReSharper disable once CppMemberFunctionMayBeConst
void EntityEventBase::Unsubscribe(const void* subscription_ptr)
{
    STACK_TRACE_ENTRY();

    if (_callbacks == nullptr) {
        return;
    }

    _entity->UnsubscribeEvent(_callbacks, subscription_ptr);
}

void EntityEventBase::UnsubscribeAll()
{
    STACK_TRACE_ENTRY();

    if (_callbacks == nullptr) {
        return;
    }

    _entity->UnsubscribeAllEvent(_callbackName);
    _callbacks = nullptr;
}
