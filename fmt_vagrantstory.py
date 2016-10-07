#Vagrant Story file formats
#http://datacrystal.romhacking.net/wiki/Vagrant_Story:File_formats

from inc_noesis import *

import math
import noesis
import rapi


VS_HEADER = b"H01\x00"


def registerNoesisTypes():
	handle = noesis.register("Vagrant Story Weapon", ".WEP")
	noesis.setHandlerTypeCheck(handle, VSCheckType)
	noesis.setHandlerLoadModel(handle, VSLoadWeapon)
	
	handle = noesis.register("Vagrant Story Shape", ".SHP")
	noesis.setHandlerTypeCheck(handle, VSCheckType)
	noesis.setHandlerLoadModel(handle, VSLoadModel)
	
	handle = noesis.register("Vagrant Story Sequence", ".SEQ")
	noesis.setHandlerTypeCheck(handle, VSNoCheck)
	noesis.setHandlerLoadModel(handle, VSLoadSequence)
	
	handle = noesis.register("Vagrant Story Mini Map", ".ARM")
	noesis.setHandlerTypeCheck(handle, VSNoCheck)
	noesis.setHandlerLoadModel(handle, VSLoadARM)
	
	handle = noesis.register("Vagrant Story Zone Datas", ".ZND")
	noesis.setHandlerTypeCheck(handle, VSNoCheck)
	noesis.setHandlerLoadRGBA(handle, VSLoadZND)
	
	handle = noesis.register("Vagrant Story Map Datas", ".MPD")
	noesis.setHandlerTypeCheck(handle, VSNoCheck)
	noesis.setHandlerLoadModel(handle, VSLoadMPD)
	
	handle = noesis.register("Vagrant Story Zone Unit Datas", ".ZUD")
	noesis.setHandlerTypeCheck(handle, VSNoCheck)
	noesis.setHandlerLoadModel(handle, VSLoadZUD)

	handle = noesis.register("Vagrant Story .TIM", ".TIM")
	noesis.setHandlerTypeCheck(handle, VSTIMCheck)
	noesis.setHandlerLoadRGBA(handle, VSLoadTIM)
	noesis.logPopup()
	return 1

def VSCheckType(data):
	bs = NoeBitStream(data)
	if bs.read("4s")[0] != VS_HEADER:
		return 0
	return 1
def VSNoCheck(data):
	return 1
def VSTIMCheck(data):
	bs = NoeBitStream(data)
	if bs.read(">B")[0] != 0x10:
		return 0
	return 1
def VSWEPParser(bs):
	h = bs.read("4s")[0]
	if h != VS_HEADER:
		return None
	numBones, numGroups, numTri, numQuad, numFace = bs.read("2B3H")
	numPoly = numTri+numQuad+numFace
	#print("numBones : "+str(numBones)+" 	numGroups : "+str(numGroups)+" 	numTri : "+str(numTri)+" 	numQuad : "+str(numQuad)+" 	numFace : "+str(numFace))
	dec = bs.getOffset()+4
	texturePtr1 = bs.read('I')[0]+dec #pointer to texture - $10
	bs.seek(0x30, NOESEEK_REL) # Unknown (always zero)
	texturePtr = int(bs.read('I')[0])+dec #relative pointer to texture section - $10
	groupPtr = bs.read('I')[0]+dec
	vertexPtr = bs.read('I')[0]+dec
	polygonPtr = bs.read('I')[0]+dec
	VSbones = VSBoneSection(bs, numBones)
	bones = []
	for i in range(0, len(VSbones)):
		bones.append(VSbones[i].toNoeBone())
	if groupPtr != bs.getOffset():
		bs.setOffset(groupPtr)
	groups = VSGroupSection(bs, numGroups, VSbones)
	if vertexPtr != bs.getOffset():
		bs.setOffset(vertexPtr)
	vertices = VSVertexSection(bs, groups, VSbones)
	if polygonPtr != bs.getOffset():
		bs.setOffset(polygonPtr)
	faces = VSFacesSection(bs, numPoly, numGroups, numTri, numQuad, len(vertices))
	if texturePtr != bs.getOffset():
		bs.setOffset(texturePtr)
	textures = VSTexturesSection(bs, True, True)
	materials = []
	for i in range(0, len(textures)):
		mat = NoeMaterial("mat_"+str(i), textures[i].name)
		materials.append(mat)
	meshes = VSBuildModel(bones, groups, vertices, faces, textures, materials)
	anims = []
	NMM = NoeModelMaterials(textures, materials)
	mdl = NoeModel(meshes, bones, anims, NMM)
	return mdl
def VSLoadWeapon(data, mdlList):
	bs = NoeBitStream(data)
	mdl = VSWEPParser(bs)
	mdlList.append(mdl)
	return 1
def VSSHPParser(bs):
	h = bs.read("4s")[0]
	if h != VS_HEADER:
		return None
	numBones, numGroups, numTri, numQuad, numFace = bs.read("2B3H")
	numPoly = numTri+numQuad+numFace
	overlays = []
	for i in range(0, 8):
		overlays.append(bs.read('4b'))
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
	dec = bs.getOffset()+4
	magicPtr = bs.read('I')[0] + dec # pointer to magic effects section (relative to offset $F8)
	for i in range(0, 0x18):
		bs.seek(0x2, NOESEEK_REL) # unknown (noticeable effects when casting spell
	AKAOPtr = bs.read('I')[0] + dec # relative pointer to AKAO section (relative to offset $F8)
	groupPtr = bs.read('I')[0] + dec # relative pointer to groups section (relative to offset $F8)
	vertexPtr = bs.read('I')[0] + dec # relative pointer to vertex section (relative to offset $F8)
	polygonPtr = bs.read('I')[0] + dec # relative pointer to polygon section (relative to offset $F8)
	VSbones = VSBoneSection(bs, numBones)
	bones = []
	for i in range(0, len(VSbones)):
		bones.append(VSbones[i].toNoeBone())
	groups = VSGroupSection(bs, numGroups, VSbones)
	if vertexPtr != bs.getOffset():
		bs.setOffset(vertexPtr)
	vertices = VSVertexSection(bs, groups, VSbones)
	faces = VSFacesSection(bs, numPoly, numGroups, numTri, numQuad, len(vertices))
	bs.seek(magicPtr-AKAOPtr, NOESEEK_REL)
	num = int(bs.read('I')[0])
	magicNum = int(bs.read('I')[0])
	if magicNum + bs.getOffset() < bs.getSize():
		bs.seek(magicNum, NOESEEK_REL)	
	textures = VSTexturesSection(bs, False, True)
	materials = []
	for i in range(0, len(textures)):
		materials.append(NoeMaterial("mat_"+str(i), textures[i].name))
	meshes = VSBuildModel(bones, groups, vertices, faces, textures, materials)
	anims = []
	NMM = NoeModelMaterials(textures, materials)
	mdl = NoeModel(meshes, bones, anims, NMM)
	return mdl
def VSLoadModel(data, mdlList):
	bs = NoeBitStream(data)
	mdl = VSSHPParser(bs)
	mdlList.append(mdl)
	return 1
def VSLoadSequence(data, mdlList):
	bs = NoeBitStream(data)
	basePtr = bs.getOffset()
	numSlots, numBones, size, h3 = bs.read('2H2I')
	slotPtr = int(bs.read('I')[0] + 8)
	dataPtr = slotPtr+numSlots
	numAnimations = int((dataPtr - numSlots - 16) / ( numBones * 4 + 10 ))
	animations = []
	for i in range(0, numAnimations):
		a = VSAnim()
		a.hydrate(bs, i, numBones)
		animations.append(a)
	slots = []
	for i in range(0, numSlots):
		slots.append(bs.read('b')[0])
	#print("slots : "+repr(slots))
	for i in range(0, numAnimations):
		animations[i].getData(bs, basePtr, dataPtr, animations)
	seqPath = rapi.getExtensionlessName(rapi.getInputName())
	modelPath = str(seqPath).split('_')[0]+".SHP"
	if rapi.checkFileExists(modelPath):
		modelData = rapi.loadIntoByteArray(modelPath)
		VSLoadModel(modelData, mdlList)
	model = mdlList[0]
	noeAnims = []
	for i in range(0, numAnimations):
		noeAnims.append(animations[i].build(model))
	model.setAnims(noeAnims)
	return 1
def VSLoadARM(data, mdlList):
	bs = NoeBitStream(data)
	numRooms = int(bs.read('I')[0])
	rooms = []
	for i in range (0, numRooms):
		room = VSARMRoom()
		room.hydrate(bs)
		rooms.append(room)

	for i in range (0, numRooms):
		room = rooms[i]
		room.draw(bs)

	for i in range (0, numRooms):
		room = rooms[i]
		room.seekName(bs)

	meshes = []
	for i in range (0, numRooms):
		meshes += rooms[i].build()


	textures = [NoeTexture("alpha_green", 1, 1, bytearray([ 0x76, 0xFF, 0x03, 128])), NoeTexture("alpha_blue", 1, 1, bytearray([ 0x00, 0xb0, 0xFF, 64]))]
	materials = [NoeMaterial("mat_alpha_green", "alpha_green"), NoeMaterial("mat_alpha_blue", "alpha_blue")]
	NMM = NoeModelMaterials(textures, materials)
	mdl = NoeModel(meshes, [], [], NMM)
	mdlList.append(mdl)

	return 1
def VSLoadZND(data, texList):
	p = ZNDParser(data)
	textures = p.parse()
	for i in range(0, len(textures)):
		texList.append(textures[i])
	return 1
class ZNDParser():
	def __init__(self, data):
		self.data = data
		self.buffer = None
		self.tims = []
		self.textures = []
		self.materials = []
	def parse(self):
		bs = NoeBitStream(self.data)
		mpdPtr, mpdLen, enemyPtr, enemyLen, timPtr, timLen, wave = bs.read("6IB")
		mpdNum = int(mpdLen/8)
		pads = bs.read("BHI")
		# MDP Section
		mpdLBAs = []
		mpdSizes = []
		if bs.getOffset() != mpdPtr:
			bs.setOffset(mpdPtr)
		for i in range(0, mpdNum):
			mpdLBAs.append(bs.read("I")[0])
			mpdSizes.append(bs.read("I")[0])
		numEnemies = bs.read("I")[0]
		# ZUD Section
		zudLBAs = []
		zudSizes = []
		if bs.getOffset() != enemyPtr:
			bs.setOffset(enemyPtr)
		for i in range(0, numEnemies):
			zudLBAs.append(bs.read("I")[0])
			zudSizes.append(bs.read("I")[0])

		enemies = []
		for i in range(0, numEnemies):
			nums = bs.read("H2B")
			name = bs.read("18s")[0]
			# ...

		# Textures section
		if bs.getOffset() != timPtr:
			bs.setOffset(timPtr)
		timSecLen, uk1, uk2, uk3, numTim = bs.read("5I")
		self.buffer = FrameBuffer()
		self.tims = []
		for i in range(0, numTim):
			tlen = bs.read("I")[0]
			tim = VSTIM()
			tim.parse(bs.readBytes(tlen), i, self.buffer)
			self.tims.append(tim)
			texture = tim.psedoTexture
			self.textures.append(texture)
		return self.textures
	def contains(self, matIdx):
		lm = len(self.materials)
		for i in range (0, lm):
			if self.materials[i].name == matIdx:
				return self.materials[i]
		return None
	def getTIM(self, idx):
		x = ( idx * 64 ) % 1024;
		y = math.floor( ( idx * 64 ) / 1024 )
		lt = len(self.tims)
		for i in range (0, lt):
			tim = self.tims[ i ]
			if ( tim.fx == x ):
				return tim
		return self.tims[0]
	def getMaterial(self, textureId, clutId, textures, materials):
		idx = str(textureId) + '-' + str(clutId)
		material = self.contains("mat_"+str(textureId)+"_"+str(clutId)) 
		if  material != None:
			return material
		else:
			textureTIM = self.getTIM( textureId )
			x = ( clutId * 16 ) % 1024
			y = math.floor( ( clutId * 16 ) / 1024 )
			clut = None
			lt = len(self.tims)
			for i in range (0, lt):
				tim = self.tims[ i ]
				if ( tim.fx <= x and tim.fx + tim.width > x and tim.fy <= y and tim.fy + tim.height > y ):
					clut = tim.buildCLUT( x, y )
					break
			texture = textureTIM.build( clut )
			texture.name = "tex_"+str(textureId)+"_"+str(clutId)
			material = NoeMaterial("mat_"+str(textureId)+"_"+str(clutId), texture.name)
			self.textures.append( texture )
			self.materials.append(material)
			textures.append(texture)
			materials.append(material)
			return material
def VSLoadMPD(data, mdlList):
	bs = NoeBitStream(data)
	# Header section
	ptrRoomSection, lenRoomSection, ptrClearedSection, lenClearedSection, ptrScriptSection, lenScriptSection, ptrDoorSection, lenDoorSection, ptrEnemySection, lenEnemySection, ptrTreasureSection, lenTreasureSection = bs.read("12I")
	# RoomSection
	# RoomHeader
	lenGeometrySection, lenCollisionSection, lenSubSection03, lenDoorSection, lenLightingSection, lenSubSection06, lenSubSection07, lenSubSection08, lenSubSection09, lenSubSection0A, lenSubSection0B, lenTextureEffectsSection = bs.read("12I")
	lenSubSection0D, lenSubSection0E, lenSubSection0F, lenSubSection10, lenSubSection11, lenSubSection12, lenSubSection13, lenAKAOSubSection, lenSubSection15, lenSubSection16, lenSubSection17, lenSubSection18 = bs.read("12I")
	# GeometrySection (Polygon groups)
	numGroups = bs.read("I")[0]
	groups = []
	for i in range (0, numGroups):
		g = MDPGroup()
		g.hydrate(bs)
		groups.append(g)
	for i in range (0, numGroups):
		g = groups[i]
		numTri, numQuad = bs.read("2I")
		faces = []
		for j in range (0, numTri):
			f = MDPFace(g)
			f.hydrate(bs, False)
			mesh = g.getMesh( bs, f.textureId, f.clutId )
			mesh.addFace( f )
		for j in range (0, numQuad):
			f = MDPFace(g)
			f.hydrate(bs, True)
			mesh = g.getMesh( bs, f.textureId, f.clutId )
			mesh.addFace( f )
	# CollisionSection
	# ClearedSection
	# ScriptSection 
	# ...

	textures = []
	materials = []

	MPDFileName = str(rapi.getLocalFileName(rapi.getInputName()))
	zndPath = rapi.getDirForFilePath(rapi.getInputName())+MDPToZND(MPDFileName)
	
	if rapi.checkFileExists(zndPath):
		zndDatas = rapi.loadIntoByteArray(zndPath)
		z = ZNDParser(zndDatas)
		z.parse()
	else:
		z = None

	meshes = []
	for i in range (0, numGroups):
		g = groups[i]

		tw = 256
		th = 256
		
		lgm = len(g.meshes)
		for j in range (0, lgm):
			iv = 0
			idxList = []
			posList = []
			uvList = []
			nmList = []
			m = g.meshes[j]

			lmf = len(m.faces)
			for k in range (0, lmf):
				f = m.faces[k]
				f.build()

				if (f.quad == True):
					posList.append(f.p1)
					posList.append(f.p2)
					posList.append(f.p3)
					posList.append(f.p4)
					uvList.append(NoeVec3([f.u2/tw, f.v2/th, 0]))
					uvList.append(NoeVec3([f.u3/tw, f.v3/th, 0]))
					uvList.append(NoeVec3([f.u1/tw, f.v1/th, 0]))
					uvList.append(NoeVec3([f.u4/tw, f.v4/th, 0]))
					#nmList.append(f.n)
					#nmList.append(f.n)
					#nmList.append(f.n)
					#nmList.append(f.n)
					idxList.append(iv+2)
					idxList.append(iv+1)
					idxList.append(iv+0)
					idxList.append(iv+1)
					idxList.append(iv+2)
					idxList.append(iv+3)
					iv += 4;
				else:
					posList.append(f.p1)
					posList.append(f.p2)
					posList.append(f.p3)
					uvList.append(NoeVec3([f.u2/tw, f.v2/th, 0]))
					uvList.append(NoeVec3([f.u3/tw, f.v3/th, 0]))
					uvList.append(NoeVec3([f.u1/tw, f.v1/th, 0]))
					#nmList.append(f.n)
					#nmList.append(f.n)
					#nmList.append(f.n)
					idxList.append(iv+2)
					idxList.append(iv+1)
					idxList.append(iv+0)
					iv += 3;

			if z != None:
				mat = z.getMaterial(m.textureId, m.clutId, textures, materials)
				mesh = NoeMesh(idxList, posList, "gpr_"+str(i), mat.name)
			else:
				mesh = NoeMesh(idxList, posList, "gpr_"+str(i))

			mesh.setUVs(uvList)
			meshes.append(mesh)



	NMM = NoeModelMaterials(textures, materials)
	mdl = NoeModel(meshes, [], [], NMM)

	mdlList.append(mdl)
	return 1
def VSLoadZUD(data, mdlList):
	bs = NoeBitStream(data)
	idCharacter, idWeapon, idWeaponCategory, idWeaponMaterial, idShield, idShieldMaterial, uk, pad = bs.read("8B")
	ptrCharacterSHP, lenCharacterSHP, ptrWeaponWEP, lenWeaponWEP, ptrShieldWEP, lenShieldWEP, ptrCommonSEQ, lenCommonSEQ, ptrBattleSEQ, lenBattleSEQ = bs.read("10I")
	#print("ptrCharacterSHP : "+str(ptrCharacterSHP)+" 	lenCharacterSHP : "+str(lenCharacterSHP))
	#print("ptrWeaponWEP : "+str(ptrWeaponWEP)+" 	lenWeaponWEP : "+str(lenWeaponWEP))
	#print("ptrShieldWEP : "+str(ptrShieldWEP)+" 	lenShieldWEP : "+str(lenShieldWEP))
	#print("ptrCommonSEQ : "+str(ptrCommonSEQ)+" 	lenCommonSEQ : "+str(lenCommonSEQ))
	#print("ptrBattleSEQ : "+str(ptrBattleSEQ)+" 	lenBattleSEQ : "+str(lenBattleSEQ))

	if ptrCharacterSHP != bs.getOffset():
		bs.setOffset(ptrCharacterSHP)
	if lenCharacterSHP > 0:
		char = VSSHPParser(bs)
		mdlList.append(char)
	if ptrWeaponWEP != bs.getOffset():
		bs.setOffset(ptrWeaponWEP)
	if lenWeaponWEP > 0:
		weapon = VSWEPParser(bs)
		mdlList.append(weapon)
	if ptrShieldWEP != bs.getOffset():
		bs.setOffset(ptrShieldWEP)
	if lenShieldWEP > 0:
		shield = VSWEPParser(bs)
		mdlList.append(shield)

	return 1
def VSLoadTIM(data, texList):
	bs = NoeBitStream(data)
	h, v, pad = bs.read(">BBH")
	bpp, offset, fx, fy, numColors, pal = bs.read("2I4H")	
	colors = []
	for j in range(0, numColors):
		colorData = bs.readBits(16)
		colors.append(colorData)
	uk1, uk2, pad, height, width = bs.read("2hI2H")
	cluts = []
	for x in range(0, width):
		for y in range(0, height):
			clut = bs.read('B')[0]
			cluts.append(clut)

	texture = NoeTexture("tex", width, height, None)
	pixmap = bytearray()
	for j in range(0, len(cluts)):
		if int(cluts[j]) < len(colors):
			pixmap += bytearray(color16to32(colors[int(cluts[j])]))
		else:
			pixmap += bytearray(color16to32(colors[16]))
	texture.pixelData = pixmap
	texList.append(texture)
	return 1
def VSBoneSection(bs, numBones):
	#print("VSBoneSection #"+str(bs.getOffset()))
	bones = []
	for i in range(0, numBones):
		bone = VSBone()
		bone.hydrate(bs, i, bones)
		bones.append(bone)
	return bones
def VSGroupSection(bs, numGroups, bones):
	#print("VSGroupSection #"+str(bs.getOffset()))
	groups = []
	for i in range(0, numGroups):
		group = VSGroup()
		group.hydrate(bs, bones)
		groups.append(group)
	return groups
def VSVertexSection(bs, groups, bones):
	vertices = []
	numVertices = groups[ len(groups) - 1 ].numVertices
	#print("VSVertexSection #"+str(bs.getOffset())+" 	numV : "+str(numVertices))
	g = 0	
	for i in range(0, numVertices):
		if i >= groups[g].numVertices:
			g = g+1
		
		vGroup = groups[g]
		vBone = vGroup.bone
		vertex = VSVertex()
		vertex.hydrate(bs, vGroup, vBone, i)
		vertices.append(vertex)

	return vertices
def VSFacesSection(bs, numPoly, numGroups, numTri, numQuad, vertices):
	#print("VSFacesSection #"+str(bs.getOffset()))
	faces = []
	for i in range(0, numPoly):
		face = VSFace()
		face.default()

		if ".SHP" in rapi.getInputName():
			if "26.SHP" in rapi.getInputName():
				face.BrainStorm(bs, vertices)
			elif "B1.SHP" in rapi.getInputName():
				face.BrainStorm(bs, vertices)

			if numGroups > 1:
				face.hydrate(bs)
			else:
				if i < (numTri):
					face.OpTri(bs)
				elif i < numTri + numQuad:
					face.OpQuad(bs)
				else:
					face.hydrate(bs)
		else:
			face.hydrate(bs)

		#print(repr(face))
		if face.type == 0x2C: # if quad
			if face.side == 8: # double
				faces.append(VSFace(0x24, face.size, face.side, face.alpha, 3, [face.vertices[2], face.vertices[1], face.vertices[0]], [face.uv[2], face.uv[1], face.uv[0]]))
				faces.append(VSFace(0x24, face.size, face.side, face.alpha, 3, [face.vertices[1], face.vertices[2], face.vertices[3]], [face.uv[1], face.uv[2], face.uv[3]]))
				faces.append(VSFace(0x24, face.size, face.side, face.alpha, 3, [face.vertices[0], face.vertices[1], face.vertices[2]], [face.uv[0], face.uv[1], face.uv[2]]))
				faces.append(VSFace(0x24, face.size, face.side, face.alpha, 3, [face.vertices[3], face.vertices[2], face.vertices[1]], [face.uv[3], face.uv[2], face.uv[1]]))
			else:
				faces.append(VSFace(0x24, face.size, face.side, face.alpha, 3, [face.vertices[2], face.vertices[1], face.vertices[0]], [face.uv[2], face.uv[1], face.uv[0]]))
				faces.append(VSFace(0x24, face.size, face.side, face.alpha, 3, [face.vertices[1], face.vertices[2], face.vertices[3]], [face.uv[1], face.uv[2], face.uv[3]]))
		elif face.type == 0x24: # if triangle
			if face.side == 8: # double
				faces.append(VSFace(0x24, face.size, face.side, face.alpha, 3, [face.vertices[2], face.vertices[1], face.vertices[0]], [face.uv[0], face.uv[2], face.uv[1]]))
				faces.append(VSFace(0x24, face.size, face.side, face.alpha, 3, [face.vertices[0], face.vertices[1], face.vertices[2]], [face.uv[2], face.uv[1], face.uv[0]]))
			else:
				faces.append(VSFace(0x24, face.size, face.side, face.alpha, 3, [face.vertices[2], face.vertices[1], face.vertices[0]], [face.uv[0], face.uv[2], face.uv[1]]))

	return faces
def VSTexturesSection(bs, isWep, drawTex = True):
	textures = []
	palletColors = []
	texMapSize, unk, halfW, halfH, numColor = bs.read('I4B')
	#print("texMapSize : "+str(texMapSize)+" 	unk : "+str(unk)+" 	halfW : "+str(halfW)+" 	halfH : "+str(halfH)+" 	numColor : "+str(numColor))
	numPallets = 7 if isWep == True else 2 #.WEP 7 pallets
	if numColor > 0:
		if isWep == True:
			handleColors = []
			for j in range(0, int(numColor/3)):
				colorData = bs.readBits(16)
				handleColors.append(colorData)
			for i in range(0, numPallets):
				colors = []
				colors += handleColors
				for j in range(0, int(numColor/3*2)):
					colorData = bs.readBits(16)
					colors.append(colorData)
				textures.append(NoeTexture("tex_"+str(i), halfW*2, halfH*2, None))
				palletColors.append(colors)
		else:
			for i in range(0, numPallets):
				colors = []
				for j in range(0, numColor):
					colorData = bs.readBits(16)
					colors.append(colorData)
				textures.append(NoeTexture("tex_"+str(i), halfW*2, halfH*2, None))
				palletColors.append(colors)

		cluts = []
		for x in range(0, halfW*2):
			for y in range(0, halfH*2):
				clut = bs.read('B')[0] #CLUT colour reference
				cluts.append(clut)

		for i in range(0, numPallets):
			pixmap = bytearray()
			for j in range(0, len(cluts)):
				if int(cluts[j]) < numColor:
					pixmap += bytearray(color16to32(palletColors[i][int(cluts[j])]))
				else:
					pixmap += bytearray(color16to32(palletColors[i][0]))
			textures[i].pixelData = pixmap
			if drawTex:
				texName = rapi.getInputName()+"_pal_"+str(i)+".png"
				if (rapi.checkFileExists(texName) == False):
					noesis.saveImageRGBA(texName, textures[i])

	return textures
def VSBuildModel(bones, groups, vertices, faces, textures, materials):
	meshes = []
	hasTex = True
	if len(textures) > 0:
		halfW = textures[0].width/2
		halfH = textures[0].height/2
		material = materials[0]
	else:
		hasTex = False

	if ("26.SHP" in rapi.getInputName() or "B1.SHP" in rapi.getInputName()):
		hasTex = False

	for i in range (0, len(bones)):
		idxList = []
		posList = []
		uvList = []
		wList = []
		for x in range(0, len(faces)):
			if len(faces[x].vertices) == 3 and int(faces[x].vertices[0]) < len(vertices):
				if (i == vertices[faces[x].vertices[0]].bone.index):
					for y in range(0, 3):
						if faces[x].vertices[y] < len(vertices):
							idxList.append(len(posList))
							posList.append(vertices[faces[x].vertices[y]].position + vertices[faces[x].vertices[y]].bone.offset)
							if hasTex == True:
								uvList.append(NoeVec3([faces[x].uv[y][0]/halfW/2, faces[x].uv[y][1]/halfH/2, 0]))
							indices = [vertices[faces[x].vertices[y]].bone.index]
							weights = [0.95]
							wList.append(NoeVertWeight(indices, weights))

		if len(posList)/3 >= 1:
			if hasTex == True:
				mesh = NoeMesh(idxList, posList, "mesh_"+str(i), material.name)
				mesh.setUVs(uvList)
				mesh.setWeights(wList)
			else :
				mesh = NoeMesh(idxList, posList, "mesh_"+str(i))
			meshes.append(mesh)
	return meshes

class VSBone:
	def __init__(self):
		self.index = 0
		self.name = ""
		self.length = 0
		self.parent = None
		self.parentIndex = -1
		self.parentName = None
		self.baseOffset = NoeVec3()
		self.offset = NoeVec3()
		self.mode = 0
		self.matrix = NoeMat43()
	def hydrate(self, bs, index, bones):
		self.index = index
		self.name = "bone_"+str(index)
		self.length = -int(bs.read('h')[0])
		bs.seek(0x2, NOESEEK_REL)
		self.parentIndex = bs.read('B')[0]
		self.baseOffset = NoeVec3(bs.read('3b'))
		self.offset = NoeVec3([self.baseOffset[0], self.baseOffset[1], self.baseOffset[2]])
		#print("Bone id : "+str(index)+" -> parent : "+str(self.parentIndex))
		if (self.parentIndex != -1 and int(self.parentIndex) < len(bones)):
			self.parent = bones[int(self.parentIndex)]
			self.parentName = "bone_"+str(self.parentIndex)
			#self.offset = self.offset + self.parent.offset
		# mode
		# 0 - 2 normal ?
		# 3 - 6 normal + roll 90 degrees
		# 7 - 255 absolute, different angles
		self.mode = bs.read('B')[0]
		self.matrix = NoeMat43([NoeVec3((self.length, 0.0, 0.0)), NoeVec3((0.0, 1.0, 0.0)), NoeVec3((0.0, 0.0, 1.0)), self.offset])
		bs.seek(0x7, NOESEEK_REL)
	def toNoeBone(self):
		return NoeBone(self.index, self.name, self.matrix, self.parentName, self.parentIndex)
	def __repr__(self):
		return "(VSBone #" + str(self.index) + " : " + str(self.name) + ", o:" + repr(self.offset)+ ", l:" + repr(self.length) + ")"
class VSGroup:
	def __init__(self):
		self.bone = None
		self.boneIndex = -1
		self.numVertices = 0
	def hydrate(self, bs, bones):
		self.boneIndex, self.numVertices = bs.read('hH')
		if self.boneIndex != -1:
			self.bone = bones[self.boneIndex]
		#print(self)
	def __repr__(self):
		return "(VSGroup #" + str(self.boneIndex) + " v: " + str(self.numVertices) + ")"
class VSVertex:
	def __init__(self):
		self.group = None
		self.bone = None
		self.position = NoeVec3()
		self.idx = -1
	def hydrate(self, bs, group, bone, i):
		self.idx = i
		self.group = group
		self.bone = bone
		self.position = NoeVec3(bs.read('3h'))
		bs.seek(0x2, NOESEEK_REL)
		#print(self)
	def __repr__(self):
		return "(VSVertex :" + str(self.idx) + "," + str(self.bone.index) + "," + repr(self.position) + ")"
class VSFace:
	def __init__(self, _type = 0, size = 0, side = 0, alpha = 0, verticesCount = 3, vertices = [], uv = []):
		self.type = _type
		self.size = size
		self.side = side
		self.alpha = alpha
		self.verticesCount = verticesCount
		self.vertices = vertices
		self.uv = uv
	def default(self):
		self.type = 0
		self.size = 0
		self.side = 0
		self.alpha = 0
		self.verticesCount = 3
		self.vertices = []
		self.uv = []
	def hydrate(self, bs):
		self.type, self.size, self.side, self.alpha = bs.read('4B')
		# self.side = [0, 4, 7, 8, 11]
		if self.type == 0x24:
			self.verticesCount = 3
		elif self.type == 0x2C:
			self.verticesCount = 4
		for i in range(0, self.verticesCount):
			idx = int(bs.read('H')[0]/4)
			self.vertices.append(idx)
		for i in range(0, self.verticesCount):
			self.uv.append(bs.read('2B'))
		#print(self)
	def BrainStorm(self, bs, vmax):
		vIdx = bs.read('4H')
		if ((vIdx[0]/4 < vmax) and (vIdx[1]/4 < vmax) and (vIdx[2]/4 < vmax) and (vIdx[3]/4 < vmax)): # good chance it's a quad
			self.type = 0x2C
			self.verticesCount = 4
			for i in range(0, self.verticesCount):
				idx = int(vIdx[i]/4)
				self.vertices.append(idx)
				self.uv.append([0,0])
			for i in range(0, 4):
				nums = bs.read("4B")

		else:
			if ((vIdx[0]/4 < vmax) and (vIdx[1]/4 < vmax) and (vIdx[2]/4 < vmax)):
				self.type = 0x24
				self.verticesCount = 3
				for i in range(0, self.verticesCount):
					idx = int(vIdx[i]/4)
					self.vertices.append(idx)
					self.uv.append([0,0])
				for i in range(0, 4):
					nums = bs.read("4B")
			else:
				self.type = 0x0
				###



	def OpTri(self, bs):
		self.type = 0x24
		self.verticesCount = 3
		for i in range(0, self.verticesCount):
			idx = int(bs.read('H')[0]/4)
			self.vertices.append(idx)
		for i in range(0, self.verticesCount):
			self.uv.append(bs.read('2B'))
		for i in range(0, self.verticesCount):
			nums = bs.read('I')

	def OpQuad(self, bs):
		self.type = 0x2C
		self.verticesCount = 4
		for i in range(0, self.verticesCount):
			idx = int(bs.read('H')[0]/4)
			self.vertices.append(idx)
		for i in range(0, self.verticesCount):
			self.uv.append(bs.read('2B'))
		for i in range(0, self.verticesCount):
			nums = bs.read('I')
		
	def __repr__(self):
		return "(VSFace :" +repr(self.type)+"	size:"+ repr(self.size)+"	side:"+ repr(self.side)+"	v:"+ repr(self.vertices) + ")"
class VSSimpleFace:
	def __init__(self):
		self.count = 0
		self.vertices = []
	def hydrate(self, bs, count):
		self.count = count
		self.vertices = bs.read('4B')
class VSLine:
	def __init__(self):
		self.p1 = 0
		self.p2 = 0
class VSDoor:
	def __init__(self):
		self.vid = 0
		self.exit = 0
		self.info = 0
		self.lid = 0
	def hydrate(self, bs):
		self.vid, self.exit, self.info, self.lid = bs.read('4B')
class VSARMRoom:
	def __init__(self):
		self.u1 = 0
		self.mapLength = 0
		self.zoneNumber = 0
		self.mapNumber = 0
		self.numVertices = 0
		self.vertices = []
		self.triangles = []
		self.quads = []
		self.floorLines = []
		self.wallLines = []
		self.doors = []
		self.name = ""
	def hydrate(self, bs):
		self.u1, self.mapLength, self.zoneNumber, self.mapNumber = bs.read('2I2H')
		#print("VSARMRoom : "+" 	length:"+str(self.mapLength)+" 	zoneNumber:"+str(self.zoneNumber)+" 	mapNumber:"+str(self.mapNumber))
	def draw(self, bs):
		self.numVertices = int(bs.read('I')[0])
		self.vertices = []
		for j in range (0, self.numVertices):
			v = VSVertex()
			v.hydrate(bs, None, None, j)
			self.vertices.append(v)
		
		self.numTriangles = int(bs.read('I')[0])
		self.triangles = []
		for j in range (0, self.numTriangles):
			f = VSSimpleFace()
			f.hydrate(bs, 3)
			self.triangles.append(f)
		
		self.numQuads = int(bs.read('I')[0])
		self.quads = []
		for j in range (0, self.numQuads):
			f = VSSimpleFace()
			f.hydrate(bs, 4)
			self.quads.append(f)

		self.numFloorLines = int(bs.read('I')[0])
		self.floorLines = []
		for j in range (0, self.numFloorLines):
			l = VSLine()
			l.p1, l.p2, pad = bs.read("2BH")
			self.floorLines.append(l)

		self.numWallLines = int(bs.read('I')[0])
		self.wallLines = []
		for j in range (0, self.numWallLines):
			l = VSLine()
			l.p1, l.p2, pad = bs.read("2BH")
			self.wallLines.append(l)

		self.numDoors = int(bs.read('I')[0])
		self.doors = []
		for j in range (0, self.numDoors):
			d = VSDoor()
			d.hydrate(bs)
			self.doors.append(d)
	def seekName(self, bs):
		self.name = str(bs.readBytes(24))
	def build(self):
		meshes = []
		idxList = []
		posList = []
		uvList = []
		nmList = []
		for i in range(0, len(self.vertices)):
			posList.append(self.vertices[i].position)
			uvList.append(NoeVec3([0,0,0]))
		for i in range(0, len(self.triangles)):
			idxList.append(int(self.triangles[i].vertices[2]))
			idxList.append(int(self.triangles[i].vertices[1]))
			idxList.append(int(self.triangles[i].vertices[0]))
		for i in range(0, len(self.quads)):
			idxList.append(int(self.quads[i].vertices[2]))
			idxList.append(int(self.quads[i].vertices[1]))
			idxList.append(int(self.quads[i].vertices[0]))
			idxList.append(int(self.quads[i].vertices[0]))
			idxList.append(int(self.quads[i].vertices[3]))
			idxList.append(int(self.quads[i].vertices[2]))
		if len(posList)/3 >= 1:
			mesh = NoeMesh(idxList, posList, self.name, "mat_alpha_green")
			mesh.uvs = uvList
			meshes.append(mesh)

		idxList = []
		posList = []
		for i in range(0, len(self.floorLines)):
			#idxList.append(int(self.floorLines[i].p1))
			#idxList.append(int(self.floorLines[i].p2))
			#idxList.append(int(self.floorLines[i].p1))
			pp1 = self.vertices[int(self.floorLines[i].p1)].position
			pp2 = self.vertices[int(self.floorLines[i].p2)].position

			ref = len(posList)
			idxList.append(len(posList))
			posList.append(NoeVec3([pp1[0]-0.1, pp1[1]-0.1, pp1[2]]))
			idxList.append(len(posList))
			posList.append(NoeVec3([pp1[0]+0.1, pp1[1]+0.1, pp1[2]]))
			idxList.append(len(posList))
			posList.append(NoeVec3([pp1[0], pp1[1], pp1[2]+0.1]))

			idxList.append(len(posList))
			posList.append(NoeVec3([pp2[0]-0.1, pp2[1]-0.1, pp2[2]]))
			idxList.append(len(posList))
			posList.append(NoeVec3([pp2[0]+0.1, pp2[1]+0.1, pp2[2]]))
			idxList.append(len(posList))
			posList.append(NoeVec3([pp2[0], pp2[1], pp2[2]+0.1]))

			idxList.append(ref)
			idxList.append(ref+1)
			idxList.append(ref+3)

			idxList.append(ref+1)
			idxList.append(ref+4)
			idxList.append(ref+3)

			idxList.append(ref+1)
			idxList.append(ref+4)
			idxList.append(ref+5)

			idxList.append(ref+4)
			idxList.append(ref+5)
			idxList.append(ref+2)

			idxList.append(ref+2)
			idxList.append(ref+1)
			idxList.append(ref+5)

			idxList.append(ref+2)
			idxList.append(ref)
			idxList.append(ref+3)

			idxList.append(ref+3)
			idxList.append(ref+5)
			idxList.append(ref+2)

		for i in range(0, len(self.wallLines)):
			#idxList.append(int(self.wallLines[i].p1))
			#idxList.append(int(self.wallLines[i].p2))
			#idxList.append(int(self.wallLines[i].p1))
			pp1 = self.vertices[int(self.wallLines[i].p1)].position
			pp2 = self.vertices[int(self.wallLines[i].p2)].position

			ref = len(posList)
			idxList.append(len(posList))
			posList.append(NoeVec3([pp1[0]-0.1, pp1[1]-0.1, pp1[2]]))
			idxList.append(len(posList))
			posList.append(NoeVec3([pp1[0]+0.1, pp1[1]+0.1, pp1[2]]))
			idxList.append(len(posList))
			posList.append(NoeVec3([pp1[0], pp1[1], pp1[2]+0.1]))

			idxList.append(len(posList))
			posList.append(NoeVec3([pp2[0]-0.1, pp2[1]-0.1, pp2[2]]))
			idxList.append(len(posList))
			posList.append(NoeVec3([pp2[0]+0.1, pp2[1]+0.1, pp2[2]]))
			idxList.append(len(posList))
			posList.append(NoeVec3([pp2[0], pp2[1], pp2[2]+0.1]))


			idxList.append(ref)
			idxList.append(ref+1)
			idxList.append(ref+3)

			idxList.append(ref+1)
			idxList.append(ref+4)
			idxList.append(ref+3)

			idxList.append(ref+1)
			idxList.append(ref+4)
			idxList.append(ref+5)

			idxList.append(ref+4)
			idxList.append(ref+5)
			idxList.append(ref+2)

			idxList.append(ref+2)
			idxList.append(ref+1)
			idxList.append(ref+5)

			idxList.append(ref+2)
			idxList.append(ref)
			idxList.append(ref+3)

			idxList.append(ref+3)
			idxList.append(ref+5)
			idxList.append(ref+2)

		uvList = []
		for i in range (0, len(posList)):
			uvList.append(NoeVec3([0,0,0]))

		if len(posList)/3 >= 1:
			mesh = NoeMesh(idxList, posList, self.name+"_line", "mat_alpha_blue")
			mesh.uvs = uvList
			meshes.append(mesh)

		return meshes
	def __repr__(self):
		return "(VSARMRoom)"
class FrameBuffer:
	def __init__(self):
		self.width = 1024
		self.height = 512
		self.buffer = bytearray()
		r = self.width*self.height*4
		for i in range(0, r):
			self.buffer += b"\x00"
	def setPixel(self, x, y, c):
		i = ( y * self.width + x ) * 4
		self.buffer[ i + 0 ] = c[ 0 ]
		self.buffer[ i + 1 ] = c[ 1 ]
		self.buffer[ i + 2 ] = c[ 2 ]
		self.buffer[ i + 3 ] = c[ 3 ]
class MDPGroup:
	def __init__(self):
		self.mdp = None
		self.scale = 8
		self.head = []
		self.meshes = []
	def hydrate(self, bs):
		self.head = []
		self.head = bs.read("64B")
		if ( self.head[ 1 ] & 0x08 ) > 0:
			self.scale = 1
	def contains(self, meshIdx):
		lm = len(self.meshes)
		for i in range (0, lm):
			if self.meshes[i].idx == meshIdx:
				return self.meshes[i]
			return None
	def getMesh(self, bs, textureId, clutId):
		idx = str(textureId) + '-' + str(clutId)
		mesh = self.contains(idx)
		if mesh != None:
			return mesh
		else:
			mesh = MPDMesh(bs, self, textureId, clutId)
			self.meshes.append(mesh)
			return mesh
class MDPFace:
	def __init__(self, group):
		self.group = group
		self.quad = False
		self.type = 0
		self.p1x = self.p1y = self.p1z = self.r1 = self.g1 = self.b1 = self.u1 = self.v1 = 0
		self.p2x = self.p2y = self.p2z = self.r2 = self.g2 = self.b2 = self.u2 = self.v2 = 0
		self.p3x = self.p3y = self.p3z = self.r3 = self.g3 = self.b3 = self.u3 = self.v3 = 0
		self.p4x = self.p4y = self.p4z = self.r4 = self.g4 = self.b4 = self.u4 = self.v4 = 0
		self.clutId = 0
		self.textureId = 0
		self.p1 = self.p2 = self.p3 = self.p4 = self.n = NoeVec3([0,0,0])
	def hydrate(self, bs, isQuad):
		self.quad = isQuad;
		self.p1x, self.p1y, self.p1z = bs.read("3h")
		self.p2x, self.p2y, self.p2z = bs.read("3b")
		self.p3x, self.p3y, self.p3z = bs.read("3b")
		self.r1, self.g1, self.b1, self.type = bs.read("4B")
		self.r2, self.g2, self.b2, self.u1, self.r3, self.g3, self.b3, self.v1, self.u2, self.v2 = bs.read("10B")
		self.clutId, self.u3, self.v3, self.textureId = bs.read("H2BH")
		if self.quad == True:
			self.p4x, self.p4y, self.p4z, self.u4, self.r4, self.g4, self.b4, self.v4 = bs.read("3b5B")
	def build(self):
		self.p1 = NoeVec3( [self.p1x, self.p1y, self.p1z] )
		self.p2 = NoeVec3( [self.p2x * self.group.scale + self.p1x, self.p2y * self.group.scale + self.p1y, self.p2z * self.group.scale + self.p1z] )
		self.p3 = NoeVec3( [self.p3x * self.group.scale + self.p1x, self.p3y * self.group.scale + self.p1y, self.p3z * self.group.scale + self.p1z] )
		if self.quad == True:
			self.p4 = NoeVec3( [self.p4x * self.group.scale + self.p1x, self.p4y * self.group.scale + self.p1y, self.p4z * self.group.scale + self.p1z] )

		#self.n = NoeVec3( [self.p2x, self.p2y, self.p2z] )
		#self.n.cross( NoeVec3( [self.p3x, self.p3y, self.p3z] ) )
		#self.n.normalize();
		#self.n = -self.n
class VSTIM():
	def __init__(self):
		self.h = 0
		self.bpp = 0
		self.imgLen = 0
		self.fx = 0
		self.fy = 0
		self.width = 0
		self.height = 0
		self.dataLen = 0
		self.dataPtr = 0
		self.psedoTexture = None
		self.data = None
		self.idx = ""
		self.texture = None
	def parse(self, data, idx, fb):
		self.idx = idx
		self.data = data
		bs = NoeBitStream(self.data)
		self.h, self.bpp, self.imgLen, self.fx, self.fy, self.width, self.height  = bs.read("3I4H")
		self.dataLen = self.imgLen - 12
		self.dataPtr = bs.getOffset()
		#bs.setOffset(dataPtr)
		pixmap = bytearray()
		for x in range(0, self.width):
			for y in range(0, self.height):
				c = color16to32(bs.readBits(16))
				pixmap += bytearray(c)
				fb.setPixel( self.fx + x, self.fy + y, c )

		self.psedoTexture = NoeTexture("tim_"+str(self.idx), self.width, self.height, pixmap)
	def buildCLUT(self, x, y):
		ox = x - self.fx
		oy = y - self.fy
		bs = NoeBitStream(self.data)
		bs.setOffset(self.dataPtr + ( oy * self.width + ox ) * 2)
		bufferArray = []
		for i in range(0, 16):
			c = color16to32(bs.readBits(16))
			bufferArray.append(c[ 0 ])
			bufferArray.append(c[ 1 ])
			bufferArray.append(c[ 2 ])
			bufferArray.append(c[ 3 ])
		return bufferArray
	def build(self, clut):
		bs = NoeBitStream(self.data)
		bs.setOffset(self.dataPtr)
		size = self.width * self.height * 2
		pixmap = bytearray()
		for i in range(0, size):
			c = bs.read("B")[0]
			l = ( ( c & 0xF0 ) >> 4 ) * 4
			r = ( c & 0x0F ) * 4
			pixmap += bytearray([clut[ r + 0 ], clut[ r + 1 ], clut[ r + 2 ], clut[ r + 3 ]])
			pixmap += bytearray([clut[ l + 0 ], clut[ l + 1 ], clut[ l + 2 ], clut[ l + 3 ]])
		self.texture = NoeTexture("tim_"+str(self.idx), self.width*4, self.height, pixmap)

		return self.texture
class MPDMesh:
	def __init__(self, bs, group, textureId, clutId):
		self.idx = str(textureId) + '-' + str(clutId)
		self.group = group
		self.textureId = textureId
		self.clutId = clutId
		self.faces = []
		self.material = None
	def addFace(self, face):
		self.faces.append(face)

class VSAnim:
	def __init__(self):
		self.idx = 0
		self.length = 0
		self.idOtherAnimation = 0
		self.mode = 0
		self.ptr1 = 0
		self.ptrTranslation = 0
		self.ptrMove = 0
		self.ptrBones = []
		self.numBones = 0
		self.pose = []
		self.keyframes = []
		self.trans = []
	def hydrate(self, bs, index, numBones):
		self.idx = index;
		self.numBones = numBones;
		self.length = bs.read('H')[0]
		# some animations use a different animation as base
		self.idOtherAnimation = bs.read('b')[0]
		self.mode = bs.read('B')[0] # unknown. has weird effects on mesh. 4
		self.ptr1 = bs.read('H')[0] # seems to point to a data block that controls looping
		self.ptrTranslation = int(bs.read('H')[0]) # points to a translation vector for the animated mesh
		self.ptrMove = bs.read('H')[0] # points to a data block that controls movement
		self.ptrBones = [] # read pointers to pose and keyframes for individual bones

		for i in range(0, self.numBones):
			self.ptrBones.append( int(bs.read('H')[0]) )
			
		for i in range(0, self.numBones):
			bs.seek(0x2, NOESEEK_REL)
	def getData(self, bs, basePtr, dataPtr, animations):
		localPtr = self.ptrTranslation+basePtr+dataPtr
		bs.setOffset(localPtr)
		x, y, z = bs.read('>3h')# BIG_ENDIAN
		#print("x : "+str(x)+" 	y : "+str(y)+" 	z : "+str(z))
		self.trans.append(NoeVec3([x, y, z]))
		
		if self.idOtherAnimation != -1:
			self = animations[ self.idOtherAnimation ]

		for i in range(0, self.numBones):
			self.keyframes.append( [ [ 0, 0, 0, 0 ] ] )
			localPtr2 = self.ptrBones[i]+basePtr+dataPtr
			bs.setOffset(localPtr2)
			rx, ry, rz = bs.read('>3h')# BIG_ENDIAN
			#print("rx : "+str(rx)+" 	ry : "+str(ry)+" 	rz : "+str(rz))
			self.pose.append([ rx, ry, rz ])
			# readKeyframes
			f = 0;
			while True:
				op = self.readOpcode(bs)
				if ( op == None ):
					break
				f += op[ 3 ]
				self.keyframes[ i ].append( op )
				if ( f >= self.length - 1 ):
					break
	def readOpcode(self, bs):
		op = bs.read('B')[0]
		op0 = op
		if ( op == 0 ):
			return None
		x = 0
		y = 0
		z = 0
		f = 0
		if ( op and 0xe0 ) > 0 :
			f = op & 0x1f
			if f == 0x1f :
				f = 0x20 + bs.read('B')[0]
			else:
				f = 1+f
		else:
			f = op & 0x3
			if f == 0x3 :
				f = 4 + bs.read('B')[0]
			else:
				f = 1+f
			
			op = op << 3
			h = bs.read('>h')[0] # BIG_ENDIAN
			
			if ( h and 0x4 ) > 0 :
				x = h >> 3
				op = op & 0x60
				
				if ( h and 0x2 ) > 0 :
					y = bs.read('>h')[0] # BIG_ENDIAN
					op = op & 0xa0

				if ( h and 0x1 ) > 0 :
					z = bs.read('>h')[0] # BIG_ENDIAN
					op = op & 0xc0
			elif ( h and 0x2 ) > 0 :
				y = h >> 3
				op = op & 0xa0
				if ( h and 0x1 ) > 0 :
					z = bs.read('>h')[0] # BIG_ENDIAN
					op = op & 0xc0
			elif ( h and 0x1 ) > 0 :
				z = h >> 3
				op = op & 0xc0
		# byte values (fallthrough)
		if ( op and 0x80 ) > 0 :
			x = bs.read('b')[0]
		if ( op and 0x40 ) > 0 :
			y = bs.read('b')[0]
		if ( op and 0x20 ) > 0 :
			z = bs.read('b')[0]
		return [ x, y, z, f ]
	def build(self, model):
		animName = "anim_"+str(self.idx)
		numAnimBones = self.numBones
		animBones = model.bones
		animNumFrames = 0
		animFrameRate = 24
		numFrameMats = len(self.pose)
		animFrameMats = []
		kfBones = []
		for i in range(0, numAnimBones):
			if i < len(self.keyframes):
				keyframes = self.keyframes[i]
				pose = self.pose[i]
				_rx = pose[0]*2
				_ry = pose[1]*2
				_rz = pose[2]*2
				keys = []
				t = 0
				kfl = len(keyframes)
				matrix = model.bones[i].getMatrix()
				animNumFrames += kfl
				kfBone = NoeKeyFramedBone(i)
				ktrss = []
				krots = []
				kscls = []
				if i > 0:
					ktrss.append(NoeKeyFramedValue(0.0, NoeVec3((matrix[0][0], 0, 0))))
				kscls.append(NoeKeyFramedValue(0.0, 1.0))
				for j in range(0, kfl):
					keyframe = keyframes[ j ]
					f = keyframe[ 3 ]
					t += f
					if keyframe[0] == None:
						keyframe[0] = keyframes[j-1][0]
					if keyframe[1] == None:
						keyframe[1] = keyframes[j-1][1]
					if keyframe[2] == None:
						keyframe[2] = keyframes[j-1][2]
					rx = rot13toRad(_rx + keyframe[0]*f)
					ry = rot13toRad(_ry + keyframe[1]*f)
					rz = rot13toRad(_rz + keyframe[2]*f)
					q = NoeQuat()
					qu = quatFromAxisAnle( NoeVec3( (1, 0, 0) ), rx )
					qv = quatFromAxisAnle( NoeVec3( (0, 1, 0) ), ry )
					qw = quatFromAxisAnle( NoeVec3( (0, 0, 1) ), rz )
					q = qw * qv * qu


					angles = NoeAngles((rx, ry, rz)).toDegrees().toQuat()

					time = t*0.04
					krots.append(NoeKeyFramedValue(time, q))

				kfBone.setTranslation(ktrss, noesis.NOEKF_TRANSLATION_VECTOR_3, noesis.NOEKF_INTERPOLATE_LINEAR)
				kfBone.setRotation(krots, noesis.NOEKF_ROTATION_QUATERNION_4, noesis.NOEKF_INTERPOLATE_LINEAR)
				kfBone.setScale(kscls, noesis.NOEKF_SCALE_SCALAR_1, noesis.NOEKF_INTERPOLATE_LINEAR)
				kfBones.append(kfBone)

		kAnim = NoeKeyFramedAnim(animName, model.bones, kfBones, 24.0)
		return kAnim

def quatFromAxisAnle(axis, angle):
	halfAngle = angle / 2
	s = math.sin( halfAngle )
	_x = axis[0] * s
	_y = axis[1] * s
	_z = axis[2] * s
	_w = math.cos( halfAngle )
	return NoeQuat((_x, _y, _z, _w))
def color16to32( c ):
	b = ( c & 0x7C00 ) >> 10
	g = ( c & 0x03E0 ) >> 5
	r = ( c & 0x001F )
	if c == 0 :
		return [ 0, 0, 0, 0 ]
	return [ r * 8, g * 8, b * 8, 255 ]
def rot13toRad(angle):
	return angle*(1/4096)*math.pi












def MDPToZND(mdpName):
	# http://datacrystal.romhacking.net/wiki/Vagrant_Story:rooms_list
	table = []
	table.append([])
	table.append([])
	table.append([])
	table.append([])
	table.append([])
	table.append([])
	table.append([])
	table.append([])
	table.append([])
	table.append(["MAP009.MPD", "MAP010.MPD", "MAP011.MPD", "MAP012.MPD", "MAP013.MPD", "MAP014.MPD", "MAP015.MPD", "MAP016.MPD", "MAP017.MPD", "MAP018.MPD", "MAP019.MPD", "MAP020.MPD", "MAP021.MPD", "MAP022.MPD", "MAP023.MPD", "MAP024.MPD", "MAP027.MPD", "MAP409.MPD"])
	table.append(["MAP211.MPD"]) # 10 Ashley and Merlose outside the Wine Cellar gate
	table.append(["MAP025.MPD"])
	table.append(["MAP026.MPD", "MAP408.MPD"])
	table.append(["MAP028.MPD", "MAP029.MPD", "MAP030.MPD", "MAP031.MPD", "MAP032.MPD", "MAP033.MPD", "MAP034.MPD", "MAP035.MPD", "MAP036.MPD", "MAP037.MPD", "MAP038.MPD", "MAP039.MPD", "MAP040.MPD", "MAP041.MPD", "MAP042.MPD", "MAP043.MPD", "MAP044.MPD", "MAP045.MPD"])
	table.append(["MAP046.MPD"]) # 14
	table.append(["MAP047.MPD", "MAP048.MPD", "MAP049.MPD", "MAP050.MPD", "MAP051.MPD", "MAP052.MPD", "MAP053.MPD", "MAP054.MPD", "MAP055.MPD", "MAP056.MPD", "MAP057.MPD", "MAP058.MPD", "MAP059.MPD"]) # 15
	table.append(["MAP060.MPD"]) # 16
	table.append(["MAP061.MPD"]) # 17
	table.append(["MAP062.MPD"]) # 18 Bardorba and Rosencrantz
	table.append(["MAP212.MPD"]) # 19 Ashley's flashback
	table.append(["MAP213.MPD"]) # 20 VKP briefing
	table.append(["MAP214.MPD"]) # 21 Ashley meets Merlose outside manor
	table.append(["MAP063.MPD", "MAP064.MPD", "MAP065.MPD", "MAP066.MPD", "MAP067.MPD", "MAP068.MPD", "MAP069.MPD", "MAP070.MPD", "MAP071.MPD", "MAP072.MPD"]) # 22
	table.append(["MAP073.MPD", "MAP074.MPD", "MAP075.MPD", "MAP076.MPD", "MAP077.MPD", "MAP078.MPD"]) # 23
	table.append(["MAP079.MPD", "MAP080.MPD", "MAP081.MPD", "MAP082.MPD", "MAP083.MPD", "MAP084.MPD", "MAP085.MPD", "MAP086.MPD", "MAP087.MPD", "MAP088.MPD", "MAP089.MPD", "MAP090.MPD", "MAP091.MPD", "MAP092.MPD", "MAP093.MPD", "MAP094.MPD"]) # 24
	table.append(["MAP095.MPD", "MAP096.MPD", "MAP097.MPD", "MAP098.MPD", "MAP099.MPD"]) # 25
	table.append(["MAP100.MPD"]) # 26 Ashley finds Sydney in the Cathedral
	table.append(["MAP101.MPD", "MAP102.MPD"]) # 27
	table.append(["MAP105.MPD", "MAP106.MPD", "MAP107.MPD", "MAP108.MPD", "MAP109.MPD", "MAP110.MPD", "MAP111.MPD", "MAP112.MPD", "MAP113.MPD", "MAP114.MPD", "MAP115.MPD", "MAP116.MPD", "MAP117.MPD", "MAP118.MPD", "MAP119.MPD", "MAP120.MPD", "MAP121.MPD", "MAP122.MPD", "MAP123.MPD"]) # 28
	table.append(["MAP124.MPD", "MAP125.MPD", "MAP126.MPD", "MAP127.MPD", "MAP128.MPD", "MAP129.MPD", "MAP130.MPD"]) # 29
	table.append(["MAP139.MPD", "MAP140.MPD", "MAP141.MPD", "MAP142.MPD", "MAP143.MPD", "MAP144.MPD"]) # 30
	table.append(["MAP145.MPD", "MAP146.MPD"])
	table.append(["MAP147.MPD", "MAP148.MPD", "MAP149.MPD", "MAP150.MPD", "MAP151.MPD", "MAP152.MPD", "MAP153.MPD", "MAP154.MPD", "MAP155.MPD", "MAP156.MPD", "MAP157.MPD", "MAP158.MPD", "MAP159.MPD", "MAP160.MPD", "MAP161.MPD", "MAP162.MPD", "MAP163.MPD", "MAP164.MPD", "MAP165.MPD", "MAP166.MPD", "MAP167.MPD", "MAP168.MPD", "MAP169.MPD", "MAP170.MPD"])
	table.append(["MAP172.MPD"]) # 33 Merlose finds corpses at Leà Monde's entrance
	table.append(["MAP173.MPD"]) # 34 Dinas Walk
	table.append(["MAP174.MPD"]) # 35
	table.append(["MAP175.MPD"]) # 36 Gharmes Walk
	table.append(["MAP176.MPD"]) # 37
	table.append(["MAP177.MPD"]) # 38 The House Gilgitte
	table.append(["MAP171.MPD"]) # 39 Plateia Lumitar
	table.append([]) # 40
	table.append([]) # 41
	table.append(["MAP205.MPD"]) # 42 Workshop "Work of Art"
	table.append(["MAP206.MPD"]) # 43 Workshop "Magic Hammer"
	table.append(["MAP207.MPD"]) # 44 Wkshop "Keane's Crafts"
	table.append(["MAP208.MPD"]) # 45 Workshop "Metal Works"
	table.append(["MAP209.MPD"]) # 46 Wkshop "Junction Point"
	table.append(["MAP210.MPD"]) # 47 Workshop "Godhands"
	table.append([]) # 48
	table.append([]) # 49
	table.append(["MAP260.MPD", "MAP261.MPD", "MAP262.MPD", "MAP263.MPD", "MAP264.MPD", "MAP265.MPD", "MAP266.MPD", "MAP267.MPD", "MAP268.MPD", "MAP269.MPD", "MAP270.MPD", "MAP271.MPD", "MAP272.MPD", "MAP273.MPD", "MAP274.MPD", "MAP275.MPD", "MAP276.MPD", "MAP277.MPD", "MAP278.MPD", "MAP279.MPD", "MAP280.MPD", "MAP281.MPD", "MAP282.MPD", "MAP283.MPD"]) # 50
	table.append([]) # 51
	table.append([]) # 52
	table.append(["MAP341.MPD"]) # 53
	table.append([]) # 54
	table.append([]) # 55
	table.append([]) # 56
	table.append(["MAP103.MPD"])
	table.append(["MAP104.MPD"])
	table.append(["MAP413.MPD"])
	table.append(["MAP131.MPD"]) # 60
	table.append(["MAP132.MPD"])
	table.append(["MAP133.MPD"])
	table.append(["MAP134.MPD"])
	table.append(["MAP135.MPD"])
	table.append(["MAP136.MPD"])
	table.append(["MAP137.MPD"])
	table.append(["MAP138.MPD"])
	table.append(["MAP178.MPD"])
	table.append(["MAP414.MPD"])
	table.append(["MAP415.MPD"]) # 70
	for i in range (0, 25):
		table.append([])
	table.append(["MAP427.MPD"]) # 96
	table.append(["MAP428.MPD"]) # 97
	table.append(["MAP429.MPD"]) # 98
	table.append(["MAP430.MPD"]) # 99
	table.append(["MAP000.MPD"]) # 100
	for i in range (0, 149):
		table.append([])
	table.append(["MAP506.MPD"]) # 250

	for i in range(0, len(table)):
		for j in range(0, len(table[i])):
			if mdpName == table[i][j]:
				ZNDId = str(i)
				if len(ZNDId) < 3:
					ZNDId = "0"+ZNDId
				if len(ZNDId) < 3:
					ZNDId = "0"+ZNDId
				return "ZONE"+ZNDId+".ZND"

	return "ZONE032.ZND"