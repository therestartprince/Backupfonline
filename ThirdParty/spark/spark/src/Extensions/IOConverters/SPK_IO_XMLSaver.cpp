//
// SPARK particle engine
//
// Copyright (C) 2008-2011 - Julien Fryer - julienfryer@gmail.com
// Copyright (C) 2017 - Frederic Martin - fredakilla@gmail.com
//
// This software is provided 'as-is', without any express or implied
// warranty.  In no event will the authors be held liable for any damages
// arising from the use of this software.
//
// Permission is granted to anyone to use this software for any purpose,
// including commercial applications, and to alter it and redistribute it
// freely, subject to the following restrictions:
//
// 1. The origin of this software must not be misrepresented; you must not
//    claim that you wrote the original software. If you use this software
//    in a product, an acknowledgment in the product documentation would be
//    appreciated but is not required.
// 2. Altered source versions must be plainly marked as such, and must not be
//    misrepresented as being the original software.
// 3. This notice may not be removed or altered from any source distribution.
//

#ifndef SPK_NO_XML

#include <ctime>

//#include <Urho3D/ThirdParty/PugiXml/pugixml.hpp>
#include <pugixml.hpp>

#include <SPARK_Core.h>
#include "Extensions/IOConverters/SPK_IO_XMLSaver.h"

namespace SPK
{
namespace IO
{
    bool XMLSaver::innerSave(std::ostream& os,Graph& graph,const std::string& filepath) const
	{
		pugi::xml_document doc;

		// Header
		//time_t currentTime = time(NULL);
		//tm* timeinfo = localtime(&currentTime);
		//std::string headerComment(" File automatically generated by SPARK on ");
		//headerComment += asctime(timeinfo);
		//headerComment.replace(headerComment.size() - 1,1,1,' '); // replace the '\n' generated by a space
		//doc.append_child(pugi::node_comment).set_value(headerComment.c_str());
		//if (!author.empty())
		//	doc.append_child(pugi::node_comment).set_value((" Author : " + author + " ").c_str());

		// Root
		pugi::xml_node root = doc.append_child("SPARK");

		Node* node = NULL;
		while ((node = graph.getNextNode()) != NULL)
			if (!node->isProcessed())
				if (!writeNode(root,*node,graph))
					return false;

        //doc.save(os,layout.indent.c_str(),layout.lineBreak ? (pugi::format_default) : (pugi::format_default | pugi::format_raw));
        doc.save_file(filepath.c_str(),layout.indent.c_str(),layout.lineBreak ? (pugi::format_default) : (pugi::format_default | pugi::format_raw));
		return true;
	}

	pugi::xml_attribute XMLSaver::getAttribute(pugi::xml_node& n, const std::string& name)
	{
		if(!n.attribute(name.c_str())) return n.append_attribute(name.c_str());
		else return n.attribute(name.c_str());
	}

	void XMLSaver::writeValue(pugi::xml_node& attrib,const std::string& value) const
	{
		switch(layout.valueLayout)
		{
		case XML_VALUE_LAYOUT_AS_ATTRIBUTE : getAttribute(attrib,"value").set_value(value.c_str()); break;
		case XML_VALUE_LAYOUT_AS_TEXT : attrib.append_child(pugi::node_pcdata).set_value(value.c_str()); break;
		}
	}

	void XMLSaver::writeRef(pugi::xml_node& attrib,const Node& node) const
	{
		std::string refStr(format(node.getReferenceID()));
		switch(layout.valueLayout)
		{
		case XML_VALUE_LAYOUT_AS_ATTRIBUTE : getAttribute(attrib,"ref").set_value(refStr.c_str()); break;
		case XML_VALUE_LAYOUT_AS_TEXT : attrib.append_child(pugi::node_pcdata).set_value(refStr.c_str()); break;
		}
	}

	bool XMLSaver::writeObject(pugi::xml_node& parent,const Ref<SPKObject>& object,Graph& graph,bool refInTag) const
	{
		Node* refNode = graph.getNode(object);
		if (refNode == NULL)
		{
			SPK_LOG_FATAL("XMLSaver::writeObject(pugi::xml_node&,const Ref<SPKObject>&,Graph&,bool) - No Node found for the object");
			return false;
		}
		if ((layout.referenceRule == XML_REFERENCE_RULE_WHEN_NEEDED && refNode->getNbReferences() > 1)
			|| layout.referenceRule == XML_REFERENCE_RULE_FORCED
			|| (layout.referenceRule == XML_REFERENCE_RULE_DESCRIBED_AT_FIRST && refNode->isProcessed()))
		{
			if (refInTag) {
			    pugi::xml_node xmlNode = parent.append_child("Ref");
				writeRef(xmlNode,*refNode);
			}
			else
				writeRef(parent,*refNode);
			return true;
		}
		else
			return writeNode(parent,*refNode,graph);
	}

	bool XMLSaver::writeNode(pugi::xml_node& parent,const Node& node,Graph& graph) const
	{
		const Descriptor& desc = node.getDescriptor();

		pugi::xml_node element = parent.append_child(desc.getName().c_str());

		for (size_t i = 0; i < desc.getNbAttributes(); ++i)
		{
			const Attribute& attrib = desc.getAttribute(i);
			if (attrib.hasValue() && !attrib.isValueOptional())
			{
				if (attrib.getName() == "name")
					getAttribute(element,"name").set_value(attrib.getValue<std::string>().c_str());
				else
				{
					pugi::xml_node child = element.append_child("attrib");
					child.append_attribute("id").set_value(attrib.getName().c_str());

					switch (attrib.getType())
					{
					case ATTRIBUTE_TYPE_CHAR :		writeValue(child,format(attrib.getValue<char>())); break;
					case ATTRIBUTE_TYPE_BOOL :		writeValue(child,format(attrib.getValue<bool>())); break;
					case ATTRIBUTE_TYPE_INT32 :		writeValue(child,format(attrib.getValue<int32>())); break;
					case ATTRIBUTE_TYPE_UINT32 :	writeValue(child,format(attrib.getValue<uint32>())); break;
					case ATTRIBUTE_TYPE_FLOAT :		writeValue(child,format(attrib.getValue<float>())); break;
					case ATTRIBUTE_TYPE_VECTOR :	writeValue(child,format(attrib.getValue<Vector3D>())); break;
					case ATTRIBUTE_TYPE_COLOR :		writeValue(child,format(attrib.getValue<Color>())); break;
					case ATTRIBUTE_TYPE_STRING :	writeValue(child,format(attrib.getValue<std::string>())); break;

					case ATTRIBUTE_TYPE_CHARS :		writeValue(child,formatArray(attrib.getValues<char>())); break;
					case ATTRIBUTE_TYPE_BOOLS :		writeValue(child,formatArray(attrib.getValues<bool>())); break;
					case ATTRIBUTE_TYPE_INT32S :	writeValue(child,formatArray(attrib.getValues<int32>())); break;
					case ATTRIBUTE_TYPE_UINT32S :	writeValue(child,formatArray(attrib.getValues<uint32>())); break;
					case ATTRIBUTE_TYPE_FLOATS :	writeValue(child,formatArray(attrib.getValues<float>())); break;
					case ATTRIBUTE_TYPE_VECTORS :	writeValue(child,formatArray(attrib.getValues<Vector3D>())); break;
					case ATTRIBUTE_TYPE_COLORS :	writeValue(child,formatArray(attrib.getValues<Color>())); break;
					case ATTRIBUTE_TYPE_STRINGS :	writeValue(child,formatArray(attrib.getValues<std::string>())); break;

					case ATTRIBUTE_TYPE_REF :
						if (!writeObject(child,attrib.getValueRef<SPKObject>(),graph,false))
							return false;
						break;

					case ATTRIBUTE_TYPE_REFS :
						{
						const std::vector<Ref<SPKObject> >& refs = attrib.getValuesRef<SPKObject>();
						for (size_t i = 0; i < refs.size(); ++i)
							if (!writeObject(child,refs[i],graph,true))
								return false;
						break;
						}

					default :
						SPK_LOG_FATAL("XMLSaver::writeNode(pugi::xml_node&,const Node&,Graph&) - Unknown attribute type");
					}
				}
			}
		}

		if (node.getNbReferences() > 1 || layout.referenceRule == XML_REFERENCE_RULE_FORCED)
			getAttribute(element,"ref").set_value(format(node.getReferenceID()).c_str());
		node.markAsProcessed();
		return true;
	}
}}
#endif
