#Vagrant Story file formats
#http://datacrystal.romhacking.net/wiki/Vagrant_Story:File_formats

from inc_noesis import *

import noesis

#rapi methods should only be used during handler callbacks
import rapi

#registerNoesisTypes is called by Noesis to allow the script to register formats.
#Do not implement this function in script files unless you want them to be dedicated format modules!
def registerNoesisTypes():
	handle = noesis.register("Vagrant Story Weapon", ".WEP")
	noesis.setHandlerTypeCheck(handle, noepyCheckType)
	noesis.setHandlerLoadModel(handle, vsLoadWeapon)
	noesis.setHandlerWriteModel(handle, vsWriteWeapon)
	
	handle = noesis.register("Vagrant Story Shape", ".SHP")
	noesis.setHandlerTypeCheck(handle, noepyCheckType)
	noesis.setHandlerLoadModel(handle, noepyLoadModel)
	noesis.setHandlerWriteModel(handle, noepyWriteModel)
	noesis.setHandlerWriteAnim(handle, noepyWriteAnim)

	noesis.logPopup()
	#print("The log can be useful for catching debug prints from preview loads.\nBut don't leave it on when you release your script, or it will probably annoy people.")
	return 1

NOEPY_HEADER = 3223624
NOEPY_VERSION = 0x00

#check if it's this type based on the data
def noepyCheckType(data):
	if len(data) < 16:
		return 0
	bs = NoeBitStream(data)
	
	if bs.readInt() != NOEPY_HEADER:
		return 0
	
	#if bs.readInt() != NOEPY_VERSION:
		#return 0
		
	return 1


def vsLoadWeapon(data, mdlList):
	bs = NoeBitStream(data)
	bs.seek(0x4, NOESEEK_REL) # signiture "H01"
	numBones = bs.read('B')[0] # number of joints in the skeleton
	numGroups = bs.read('B')[0] # number of groups
	numTri = bs.read('H')[0] # number of triangles in the first polygon group
	numQuad = bs.read('H')[0] # number of quads in the second polygon group
	numFace = bs.read('H')[0] # number of nemain polygons (which are further grouped into triangles and quads)
	numPoly = numTri+numQuad+numFace
	
	print("numBones : "+str(numBones))
	print("numGroups : "+str(numGroups))
	print("numTri : "+str(numTri))
	print("numQuad : "+str(numQuad))
	print("numFace : "+str(numFace))
	print("numPoly : "+str(numPoly))
	
	texturePtr1 = bs.read('I')[0]+0x10 #pointer to texture - $10
	bs.seek(0x30, NOESEEK_REL) # Unknown (always zero)
	texturePtr = int(bs.read('I')[0])+0x10 #relative pointer to texture section - $10
	groupPtr = bs.read('I')[0]+0x10
	vertexPtr = bs.read('I')[0]+0x10
	polygonPtr = bs.read('I')[0]+0x10
	
	bones = []
	for i in range(0, numBones):
		bone_data = noepyReadBone(bs, i)
		bones.append(bone_data)
	
	if groupPtr != bs.getOffset():
		bs.setOffset(groupPtr)
	groups = []
	for i in range(0, numGroups):
		group_data = noepyReadGroup(bs, bones)
		groups.append(group_data)
	
	if vertexPtr != bs.getOffset():
		bs.setOffset(vertexPtr)
	numGroups = len(groups)
	numVertices = groups[ numGroups - 1 ].vertex
	print("numVertices : "+str(numVertices))
	vertexs = []
	g = 0	
	for i in range(0, numVertices):
		if i >= groups[g].vertex:
			g = g+1
		
		vGroup = groups[g]
		vBone = groups[g].boneId
		vertex_data = noepyReadVertex(bs, g, vGroup, vBone, i)
		vertexs.append(vertex_data)
	
	polygones = []
	polyPtr = bs.getOffset();
	for i in range(0, numPoly):
		poly = VS_POLY(bs, vertexs)
		if poly.polyType == 0x24:
			if poly.polySide == 8: # double
				polygones.append(Polygone(0x24, poly.polySize, poly.polySide, poly.polyAlpha, [poly.v[2], poly.v[1], poly.v[0]], [poly.uv[0], poly.uv[2], poly.uv[1]]))
				polygones.append(Polygone(0x24, poly.polySize, poly.polySide, poly.polyAlpha, [poly.v[0], poly.v[1], poly.v[2]], [poly.uv[2], poly.uv[1], poly.uv[0]]))
			else:
				polygones.append(Polygone(0x24, poly.polySize, poly.polySide, poly.polyAlpha, [poly.v[2], poly.v[1], poly.v[0]], [poly.uv[0], poly.uv[2], poly.uv[1]]))
		elif poly.polyType == 0x2C:
			if poly.polySide == 8: # double
				poly1 = Polygone(0x24, poly.polySize/2, poly.polySide, poly.polyAlpha, [poly.v[2], poly.v[1], poly.v[0]], [poly.uv[2], poly.uv[1], poly.uv[0]])
				poly2 = Polygone(0x24, poly.polySize/2, poly.polySide, poly.polyAlpha, [poly.v[1], poly.v[2], poly.v[3]], [poly.uv[1], poly.uv[2], poly.uv[3]])
				poly3 = Polygone(0x24, poly.polySize/2, poly.polySide, poly.polyAlpha, [poly.v[0], poly.v[1], poly.v[2]], [poly.uv[0], poly.uv[1], poly.uv[2]])
				poly4 = Polygone(0x24, poly.polySize/2, poly.polySide, poly.polyAlpha, [poly.v[3], poly.v[2], poly.v[1]], [poly.uv[3], poly.uv[2], poly.uv[1]])
				polygones.append(poly1)
				polygones.append(poly2)
				polygones.append(poly3)
				polygones.append(poly4)
			else:
				poly1 = Polygone(0x24, poly.polySize/2, poly.polySide, poly.polyAlpha, [poly.v[2], poly.v[1], poly.v[0]], [poly.uv[2], poly.uv[1], poly.uv[0]])
				poly2 = Polygone(0x24, poly.polySize/2, poly.polySide, poly.polyAlpha, [poly.v[1], poly.v[2], poly.v[3]], [poly.uv[1], poly.uv[2], poly.uv[3]])
				polygones.append(poly1)
				polygones.append(poly2)
	
	print("polygones len ? : "+str(len(polygones)))
	
	
	print("texturePtr1 : "+str(texturePtr1))
	print("texturePtr : "+str(texturePtr))
	print("texturePtr ? : "+str(bs.getOffset()))
	
	
	texMapSize = bs.read('I')[0]
	print("texMapSize : "+str(texMapSize))
	unk = bs.read('B')[0] #unknown
	halfW = bs.read('B')[0] #half the width in pixels
	print("halfW : "+str(halfW))
	halfH = bs.read('B')[0] #half the height in pixels
	print("halfH : "+str(halfH))
	numColor = bs.read('B')[0] #number of colours per pallet
	print("numColor : "+str(numColor))
	#.WEP 7 pallets
	palletColors = []
	textures = []
	
	handleColors = []
	for j in range(0, int(numColor/3)):
		colorData = bs.readBits(16)
		handleColors.append(colorData)
			
	for i in range(0, 7):
		colors = []
		colors = colors+handleColors
		for j in range(0, int(numColor/3*2)):
			colorData = bs.readBits(16)
			colors.append(colorData)
		textures.append(NoeTexture("tex_"+str(i), halfW*2, halfH*2, None))
		palletColors.append(colors)
	
	
	cluts = []
	for x in range(0, halfW*2):
		for y in range(0, halfH*2):
			clut = bs.read('B')[0] #CLUT colour reference
			cluts.append(clut)
	
	materials = []
	for i in range(0, 7):
		pixmap = []
		for j in range(0, len(cluts)):
			pixmap = pixmap + color16to32(palletColors[i][int(cluts[j])])
		
		texByteArray = bytearray(pixmap)
		textures[i].pixelData = texByteArray
		#texName = rapi.getInputName()+"_pal_"+str(i)+".png"
		#if (rapi.checkFileExists(texName) == False):
		#noesis.saveImageRGBA(texName, textures[i])
		materials.append(NoeMaterial("mat_"+str(i), "tex_"+str(i)))
	
	
	texList = textures
	
	meshes = []	
	posList = []
	idxList = []
	uvList = []	
	for i in range(0, numVertices):
		posList.append(NoeVec3([vertexs[i].x, vertexs[i].y, vertexs[i].z]))
		uvList.append(NoeVec3())
	
	for i in range(0, len(polygones)):
		for j in range(0, 3):
			#idxList.append(len(posList))
			#posList.append(NoeVec3([polygones[i].v[j].x, polygones[i].v[j].y, polygones[i].v[j].z]))
			idxList.append(polygones[i].v[j].idx)
			uv = NoeVec3([polygones[i].uv[j][0]/halfW/2, polygones[i].uv[j][1]/halfH/2, 0])
			uvList[polygones[i].v[j].idx] = uv
	
	mesh = NoeMesh(idxList, posList, "mesh_0", "mat_2")
	mesh.uvs = uvList
	meshes.append(mesh)	
	
	NMM = NoeModelMaterials(textures, materials)
	#class NoeModel:
	#def __init__(self, meshes = [], bones = [], anims = [], modelMats = None):
	mdl = NoeModel(meshes, bones, [], NMM)
	mdl.setBones(bones)
	mdlList.append(mdl)
	
	return 1

def vsWriteWeapon(mdl, bs):
	return 1

#load the model
def noepyLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	bs = NoeBitStream(data)
	bs.seek(0x4, NOESEEK_REL) #signiture "H01"
	numJoints = bs.read('b')[0]
	numGroups = bs.read('b')[0]
	numTri = bs.read('h')[0]
	numQuad = bs.read('h')[0]
	numFace = bs.read('h')[0]
	numPoly = numTri+numQuad+numFace
	
	print("numBones : "+str(numJoints))
	print("numGroups : "+str(numGroups))
	print("numTri : "+str(numTri))
	print("numQuad : "+str(numQuad))
	print("numPoly : "+str(numPoly))
	
	overlaysX = []
	overlaysY = []
	overlaysW = []
	overlaysH = []
	for i in range(0, 8):
		overlaysX.append(bs.read('b')[0])
		overlaysY.append(bs.read('b')[0])
		overlaysW.append(bs.read('b')[0])
		overlaysH.append(bs.read('b')[0])
	
	bs.seek(0x24, NOESEEK_REL) # Unknown
	bs.seek(0x6, NOESEEK_REL) # collision size and height (shape is a cylinder)
	bs.seek(0x2, NOESEEK_REL) # menu position Y
	bs.seek(0xC, NOESEEK_REL) # Unknown
	bs.seek(0x2, NOESEEK_REL) # Shadow radius
	bs.seek(0x2, NOESEEK_REL) # Shadow size increase rate
	bs.seek(0x2, NOESEEK_REL) # Shadow size decrease rate
	bs.seek(0x4, NOESEEK_REL) # Unknown
	bs.seek(0x2, NOESEEK_REL) # Menu scale
	bs.seek(0x2, NOESEEK_REL) # Unknown
	bs.seek(0x2, NOESEEK_REL) # Target sphere position Y
	bs.seek(0x8, NOESEEK_REL) # Unknown
	
	for i in range(0, 0xC):
		bs.seek(0x4, NOESEEK_REL) # LBA XX_BTX.SEQ  (battle animations first one is actually XX_COM.SEQ)
	
	for i in range(0, 0xC):
		bs.seek(0x2, NOESEEK_REL) # chain attack animation ID
	
	for i in range(0, 4):
		bs.seek(0x4, NOESEEK_REL) # LBA XXSP0X.SEQ (special attack animations)
		
	bs.seek(0x20, NOESEEK_REL) # unknown (probably more LBA tables, there are also special attack ids stored here.)
	magicPtr = bs.read('i')[0] + 0xF8 # pointer to magic effects section (relative to offset $F8)
	#print("magicPtr : "+str(magicPtr))
	
	for i in range(0, 0x18):
		bs.seek(0x2, NOESEEK_REL) # unknown (noticeable effects when casting spell
	
	AKAOPtr = bs.read('i')[0] + 0xF8 # relative pointer to AKAO section (relative to offset $F8)
	groupPtr = bs.read('i')[0] + 0xF8 # relative pointer to groups section (relative to offset $F8)
	vertexPtr = bs.read('i')[0] + 0xF8 # relative pointer to vertex section (relative to offset $F8)
	polygonPtr = bs.read('i')[0] + 0xF8 # relative pointer to polygon section (relative to offset $F8)
	#print("AKAOPtr : "+str(AKAOPtr))
	#print("groupPtr : "+str(groupPtr))
	#print("vertexPtr : "+str(vertexPtr))
	#print("polygonPtr : "+str(polygonPtr))

	bones = []
	for i in range(0, numJoints):
		joint_data = noepyReadBone(bs, i)
		bones.append(joint_data)
	
	groups = []
	for i in range(0, numGroups):
		group_data = noepyReadGroup(bs, bones)
		groups.append(group_data)
		
		
	numGroups = len(groups)
	numVertices = groups[ numGroups - 1 ].vertex
	print("numVertices : "+str(numVertices))
	vertexs = []
	g = 0
	vrtPtr = bs.getOffset();
	#print("vrtPtr : "+str(vrtPtr))
	for i in range(0, numVertices):
		if i >= groups[g].vertex:
			g = g+1
		
		vGroup = groups[g]
		vBone = groups[g].boneId
		vertex_data = noepyReadVertex(bs, g, vGroup, vBone, i)
		vertexs.append(vertex_data)
	
	
	# vertex OK
	
	
	polygones = []
	polyPtr = bs.getOffset();
	for i in range(0, numPoly):
		poly = VS_POLY(bs, vertexs)
		if poly.polyType == 0x24:
			if poly.polySide == 8: # double
				print("poly.polySide : "+str(poly.polySide))
				polygones.append(Polygone(0x24, poly.polySize, poly.polySide, poly.polyAlpha, [poly.v[0], poly.v[1], poly.v[2]], [poly.uv[0], poly.uv[1], poly.uv[2]]))
				polygones.append(Polygone(0x24, poly.polySize, poly.polySide, poly.polyAlpha, [poly.v[2], poly.v[1], poly.v[0]], [poly.uv[2], poly.uv[1], poly.uv[0]]))
			else:
				polygones.append(Polygone(0x24, poly.polySize, poly.polySide, poly.polyAlpha, [poly.v[0], poly.v[1], poly.v[2]], [poly.uv[0], poly.uv[1], poly.uv[2]]))
		elif poly.polyType == 0x2C:
			if poly.polySide == 8: # double
				print("poly.polySide : "+str(poly.polySide))
				poly1 = Polygone(0x24, poly.polySize/2, poly.polySide, poly.polyAlpha, [poly.v[0], poly.v[1], poly.v[2]], [poly.uv[0], poly.uv[1], poly.uv[2]])
				poly2 = Polygone(0x24, poly.polySize/2, poly.polySide, poly.polyAlpha, [poly.v[1], poly.v[2], poly.v[3]], [poly.uv[1], poly.uv[2], poly.uv[3]])
				poly3 = Polygone(0x24, poly.polySize/2, poly.polySide, poly.polyAlpha, [poly.v[2], poly.v[1], poly.v[0]], [poly.uv[2], poly.uv[1], poly.uv[0]])
				poly4 = Polygone(0x24, poly.polySize/2, poly.polySide, poly.polyAlpha, [poly.v[3], poly.v[2], poly.v[1]], [poly.uv[3], poly.uv[2], poly.uv[1]])
				polygones.append(poly1)
				polygones.append(poly2)
				polygones.append(poly3)
				polygones.append(poly4)
			else:
				poly1 = Polygone(0x24, poly.polySize/2, poly.polySide, poly.polyAlpha, [poly.v[0], poly.v[1], poly.v[2]], [poly.uv[0], poly.uv[1], poly.uv[2]])
				poly2 = Polygone(0x24, poly.polySize/2, poly.polySide, poly.polyAlpha, [poly.v[1], poly.v[2], poly.v[3]], [poly.uv[1], poly.uv[2], poly.uv[3]])
				polygones.append(poly1)
				polygones.append(poly2)
	
	print("polygones len ? : "+str(len(polygones)))
	meshes = []
	
	posList = []
	idxList = []
	uvList = []
	uvList2 = []
	
	#for i in range(0, numVertices):
		#posList.append(NoeVec3([vertexs[i].x, vertexs[i].y, vertexs[i].z]))
	
	for i in range(0, len(polygones)):
		for j in range(0, 3):
			idxList.append(len(posList))
			posList.append(NoeVec3([polygones[i].v[j].x, polygones[i].v[j].y, polygones[i].v[j].z]))
			#idxList.append(polygones[i].v[j].idx)
			uv = NoeVec3([polygones[i].uv[j][0]/128, polygones[i].uv[j][1]/128, 0])
			uvList.append(uv)		
	
	mesh = NoeMesh(idxList, posList)
	mesh.uvs = uvList
	meshes.append(mesh)	
		
	
	akaoPtr = bs.getOffset();
	bs.setOffset(magicPtr);
	bs.seek(0x4, NOESEEK_REL)
	magicNum = bs.read('i')[0]
	bs.seek(magicNum, NOESEEK_REL)
	
	texMapSize = bs.read('I')[0]
	print("texMapSize ? : "+str(texMapSize))
	unk = bs.read('B')[0] #unknown
	halfW = bs.read('B')[0] #half the width in pixels
	print("halfW ? : "+str(halfW))
	halfH = bs.read('B')[0] #half the height in pixels
	print("halfH ? : "+str(halfH))
	numColor = bs.read('B')[0] #number of colours per pallet
	print("numColor ? : "+str(numColor))
	#.SHP always with 2 pallets
	palletColors = []
	textures = []
	for i in range(0, 2):
		colors = []
		for j in range(0, numColor):
			colorData = bs.readBits(16)
			colors.append(colorData)
			textures.append(NoeTexture("Texture_"+str(i), halfW*2, halfH*2, None))
		palletColors.append(colors)
	
	
	cluts = []
	for x in range(0, halfW*2):
		for y in range(0, halfH*2):
			clut = bs.read('B')[0] #CLUT colour reference
			cluts.append(clut)
	
	materials = []
	for i in range(0, 2):
		pixmap = []
		for j in range(0, len(cluts)):
			pixmap = pixmap + color16to32(palletColors[i][cluts[j]])
			
		texByteArray = bytearray(pixmap)
		textures[i].pixelData = texByteArray
		texName = rapi.getInputName()+"_pal_"+str(i)+".png"
		if (rapi.checkFileExists(texName) == False):
			noesis.saveImageRGBA(texName, textures[i])
		materials.append(NoeMaterial(texName, texName))
	
	anims = []
	
	mesh = NoeMesh(idxList, posList, "mesh_0", materials[0].name)
	mesh.uvs = uvList
	meshes.append(mesh)	
	
	mdl = NoeModel(meshes, bones)
	mdl.setBones(bones)
	mdlList.append(mdl)
	
	return 1

	
	
#write it
def noepyWriteModel(mdl, bs):
	anims = rapi.getDeferredAnims()

	bs.writeInt(NOEPY_HEADER)
	bs.writeInt(NOEPY_VERSION)

	bs.writeInt(len(mdl.meshes))
	for mesh in mdl.meshes:
		bs.writeString(mesh.name)
		bs.writeString(mesh.matName)
		bs.writeInt(len(mesh.indices))
		bs.writeInt(len(mesh.positions))
		bs.writeInt(len(mesh.normals))
		bs.writeInt(len(mesh.uvs))
		bs.writeInt(len(mesh.tangents))
		bs.writeInt(len(mesh.colors))
		bs.writeInt(len(mesh.weights))
		for idx in mesh.indices:
			bs.writeInt(idx)
		for vcmp in mesh.positions:
			bs.writeBytes(vcmp.toBytes())
		for vcmp in mesh.normals:
			bs.writeBytes(vcmp.toBytes())
		for vcmp in mesh.uvs:
			bs.writeBytes(vcmp.toBytes())
		for vcmp in mesh.tangents:
			bs.writeBytes(vcmp.toBytes())
		for vcmp in mesh.colors:
			bs.writeBytes(vcmp.toBytes())
		for vcmp in mesh.weights:
			bs.writeInt(vcmp.numWeights())
			for wval in vcmp.indices:
				bs.writeInt(wval)
			for wval in vcmp.weights:
				bs.writeFloat(wval)
		bs.writeInt(len(mesh.morphList))
		for mf in mesh.morphList:
			bs.writeInt(len(mf.positions))
			bs.writeInt(len(mf.normals))
			for vec in mf.positions:
				bs.writeBytes(vec.toBytes())
			for vec in mf.normals:
				bs.writeBytes(vec.toBytes())

	bs.writeInt(len(mdl.bones))
	for bone in mdl.bones:
		noepyWriteBone(bs, bone)

	bs.writeInt(len(anims))
	for anim in anims:
		bs.writeString(anim.name)
		bs.writeInt(len(anim.bones))
		for bone in anim.bones:
			noepyWriteBone(bs, bone)
		bs.writeInt(anim.numFrames)
		bs.writeFloat(anim.frameRate)
		bs.writeInt(len(anim.frameMats))
		for mat in anim.frameMats:
			bs.writeBytes(mat.toBytes())

	return 1

#when you want animation data to be written out with a model format, you should make a handler like this that catches it and defers it
def noepyWriteAnim(anims, bs):
	#it's good practice for an animation-deferring handler to inform the user that the format only supports joint model-anim export
	if rapi.isGeometryTarget() == 0:
		print("WARNING: Stand-alone animations cannot be written to the .noepy format.")
		return 0

	rapi.setDeferredAnims(anims)
	return 0

#write bone
def noepyWriteBone(bs, bone):
	bs.writeInt(bone.index)
	bs.writeString(bone.name)
	bs.writeString(bone.parentName)
	bs.writeInt(bone.parentIndex)
	bs.writeBytes(bone.getMatrix().toBytes())

#read bone
def noepyReadBone(bs, index):
	#this.length = -s16(); // negative
	#skip( 2 ); // always 0xFFFF, no effect on bone size or model
	#this.parentBoneId = s8();
	#this.x = s8();
	#this.y = s8();
	#this.z = s8();
	#this.mode = s8();
	#skip( 1 ); // unknown
	#skip( 6 ); // always 0? padding?
	boneIndex = index
	boneName = "bone_"+str(index)
	boneSize = -int(bs.read('i')[0])
	#bs.seek(0x2, NOESEEK_REL)
	bonePIndex = bs.read('B')[0]
	bonePName = "bone_"+str(bonePIndex)
	
	boneX = bs.read('b')[0]
	boneY = bs.read('b')[0]
	boneZ = bs.read('b')[0]
	# mode
	# 0 - 2 normal ?
	# 3 - 6 normal + roll 90 degrees
	# 7 - 255 absolute, different angles
	boneMode = bs.read('B')[0]
	#boneMat = NoeMat43([NoeVec3((boneX, 0.0, 0.0)), NoeVec3((0.0, boneY, 0.0)), NoeVec3((0.0, 0.0, boneZ)), NoeVec3((1.0, 0.0, 0.0))])
	boneMat = NoeMat43()
	bs.seek(0x7, NOESEEK_REL)
	return NoeBone(boneIndex, boneName, boneMat, bonePName, bonePIndex)
		
def noepyReadGroup(bs, bones):
	groupJoint = bs.read('h')[0]
	groupVertex = bs.read('H')[0]
	return Group(groupJoint, groupVertex)

def noepyReadVertex(bs, g, vGroup, vBone, idx):
	x = bs.read('h')[0]
	y = bs.read('h')[0]
	z = bs.read('h')[0]
	bs.seek(0x2, NOESEEK_REL)
	#print("vertex x : "+str(x)+" - vertex y : "+str(y)+" - vertex z : "+str(z))
	return Vertex(g, vGroup, vBone, x, y, z, idx)


class Vertex:
	def __init__(self, groupId, group, boneId, x, y, z, idx):
		self.groupId = groupId;
		self.group = group;
		self.boneId = boneId;
		self.x = x;
		self.y = y;
		self.z = z;
		self.idx = idx;

class Group:
    def __init__(self, boneId, vertex):
        self.boneId = boneId
        self.vertex = vertex
		
class Polygone:
	def __init__(self, polyType, polySize, polySide, polyAlpha, v, uv):
		self.polyType = polyType
		self.polySize = polySize
		self.polySide = polySide
		self.polyAlpha = polyAlpha
		self.v = v
		self.uv = uv

def VS_POLY(bs, vertexs):
	polyType = bs.read('b')[0]
	polySize = bs.read('b')[0]
	polySide = bs.read('b')[0]
	polyAlpha = bs.read('b')[0]
	polyCount = 3
	if polyType == 0x24:
		polyCount = 3
	elif polyType == 0x2C:
		polyCount = 4
	v = []
	for i in range(0, polyCount):
		idx = bs.read('H')[0]/4
		v.append(vertexs[int(idx)])
	uv = []
	for i in range(0, polyCount):
		uv.append([bs.read('B')[0], bs.read('B')[0]])
	return Polygone(polyType, polySize, polySide, polyAlpha, v, uv)


def color16to32( c ):
	b = ( c & 0x7C00 ) >> 10
	g = ( c & 0x03E0 ) >> 5
	r = ( c & 0x001F )
	if c == 0 :
		return [ 0, 0, 0, 0 ]
	
	#5bit -> 8bit is factor 2^3 = 8
	return [ r * 8, g * 8, b * 8, 255 ]
