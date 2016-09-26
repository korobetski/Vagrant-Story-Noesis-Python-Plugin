#Vagrant Story file formats
#http://datacrystal.romhacking.net/wiki/Vagrant_Story:File_formats

from inc_noesis import *

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
	noesis.setHandlerTypeCheck(handle, VSSequenceCheck)
	noesis.setHandlerLoadModel(handle, VSLoadSequence)

	noesis.logPopup()
	return 1

def VSCheckType(data):
	bs = NoeBitStream(data)
	if bs.read("4s")[0] != VS_HEADER:
		return 0
	return 1

def VSSequenceCheck(data):
	return 1

def VSLoadWeapon(data, mdlList):
	bs = NoeBitStream(data)
	h, numBones, numGroups, numTri, numQuad, numFace = bs.read("i2B3H")
	numPoly = numTri+numQuad+numFace

	texturePtr1 = bs.read('I')[0]+0x10 #pointer to texture - $10
	bs.seek(0x30, NOESEEK_REL) # Unknown (always zero)
	texturePtr = int(bs.read('I')[0])+0x10 #relative pointer to texture section - $10
	groupPtr = bs.read('I')[0]+0x10
	vertexPtr = bs.read('I')[0]+0x10
	polygonPtr = bs.read('I')[0]+0x10

	
	VSbones = VSBoneSection(bs, numBones)
	bones = []
	for i in range(0, len(VSbones)):
		bones.append(VSbones[i].toNoeBone())
	groups = VSGroupSection(bs, numGroups, VSbones)

	if vertexPtr != bs.getOffset():
		bs.setOffset(vertexPtr)
	vertices = VSVertexSection(bs, groups, VSbones)
	faces = VSFacesSection(bs, numPoly)

	textures = VSTexturesSection(bs, True, False)
	materials = []
	for i in range(0, len(textures)):
		materials.append(NoeMaterial("mat_"+str(i), textures[i].name))
	meshes = VSBuildModel(bones, groups, vertices, faces, textures, materials)

	anims = []
	NMM = NoeModelMaterials(textures, materials)
	mdl = NoeModel(meshes, bones, anims, NMM)
	mdlList.append(mdl)

	return 1

def VSLoadModel(data, mdlList):
	bs = NoeBitStream(data)
	h, numBones, numGroups, numTri, numQuad, numFace = bs.read("i2B3H")
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
	magicPtr = bs.read('i')[0] + 0xF8 # pointer to magic effects section (relative to offset $F8)
	
	for i in range(0, 0x18):
		bs.seek(0x2, NOESEEK_REL) # unknown (noticeable effects when casting spell
	
	AKAOPtr = bs.read('i')[0] + 0xF8 # relative pointer to AKAO section (relative to offset $F8)
	groupPtr = bs.read('i')[0] + 0xF8 # relative pointer to groups section (relative to offset $F8)
	vertexPtr = bs.read('i')[0] + 0xF8 # relative pointer to vertex section (relative to offset $F8)
	polygonPtr = bs.read('i')[0] + 0xF8 # relative pointer to polygon section (relative to offset $F8)

	VSbones = VSBoneSection(bs, numBones)
	bones = []
	for i in range(0, len(VSbones)):
		bones.append(VSbones[i].toNoeBone())
	groups = VSGroupSection(bs, numGroups, VSbones)

	if vertexPtr != bs.getOffset():
		bs.setOffset(vertexPtr)
	vertices = VSVertexSection(bs, groups, VSbones)
	faces = VSFacesSection(bs, numPoly)

	akaoPtr = bs.getOffset();
	bs.setOffset(magicPtr);
	bs.seek(0x4, NOESEEK_REL)
	magicNum = bs.read('i')[0]
	bs.seek(magicNum, NOESEEK_REL)

	textures = VSTexturesSection(bs, False, False)
	materials = []
	for i in range(0, len(textures)):
		materials.append(NoeMaterial("mat_"+str(i), textures[i].name))
	meshes = VSBuildModel(bones, groups, vertices, faces, textures, materials)

	anims = []
	NMM = NoeModelMaterials(textures, materials)
	mdl = NoeModel(meshes, bones, anims, NMM)
	mdlList.append(mdl)
	return 1


def VSLoadSequence(data, mdlList):
	bs = NoeBitStream(data)
	basePtr = bs.getOffset()
	numSlots = int(bs.read('H')[0])
	numBones = bs.read('H')[0]
	size = bs.read('I')[0]
	h3 = bs.read('I')[0]
	slotPtr = int(bs.read('I')[0] + 8)
	dataPtr = slotPtr+numSlots
		
	numAnimations = int((dataPtr - numSlots - 16) / ( numBones * 4 + 10 ))
	animations = []
	for i in range(0, numAnimations):
		animations.append(VS_Anim(bs, i, numBones))
	
	slots = []
	for i in range(0, numSlots):
		slots.append(bs.read('b')[0])
	
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



def VSBoneSection(bs, numBones):
	bones = []
	for i in range(0, numBones):
		bone = VSBone()
		bone.hydrate(bs, i, bones)
		bones.append(bone)
	return bones

def VSGroupSection(bs, numGroups, bones):
	groups = []
	for i in range(0, numGroups):
		group = VSGroup()
		group.hydrate(bs, bones)
		groups.append(group)
	return groups

def VSVertexSection(bs, groups, bones):
	vertices = []
	numVertices = groups[ len(groups) - 1 ].numVertices
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

def VSFacesSection(bs, numPoly):
	faces = []
	for i in range(0, numPoly):
		face = VSFace()
		face.default()
		face.hydrate(bs)
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
	numPallets = 7 if isWep == True else 2 #.WEP 7 pallets
	if isWep == True:
		handleColors = []
		for j in range(0, int(numColor/3)):
			colorData = bs.readBits(16)
			handleColors.append(colorData)
		for i in range(0, numPallets):
			colors = []
			colors = colors+handleColors
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
		pixmap = []
		for j in range(0, len(cluts)):
			pixmap = pixmap + color16to32(palletColors[i][int(cluts[j])])
		textures[i].pixelData = bytearray(pixmap)
		if drawTex:
			texName = rapi.getInputName()+"_pal_"+str(i)+".png"
			if (rapi.checkFileExists(texName) == False):
				noesis.saveImageRGBA(texName, textures[i])

	return textures

def VSBuildModel(bones, groups, vertices, faces, textures, materials):
	meshes = []
	halfW = textures[0].width/2
	halfH = textures[0].height/2
	material = materials[0]
	for i in range (0, len(bones)):
		idxList = []
		posList = []
		uvList = []
		for x in range(0, len(faces)):
			if (True if i == vertices[faces[x].vertices[0]].bone.index else False):
				for y in range(0, 3):
					idxList.append(len(posList))
					posList.append(vertices[faces[x].vertices[y]].position)
					uvList.append(NoeVec3([faces[x].uv[y][0]/halfW/2, faces[x].uv[y][1]/halfH/2, 0]))

		if len(posList)/3 >= 1:
			mesh = NoeMesh(idxList, posList, "mesh_"+str(i), material.name)
			mesh.uvs = uvList
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
		if (self.parentIndex != -1 & int(self.parentIndex) < len(bones)):
			self.parent = bones[int(self.parentIndex)]
			self.parentName = "bone_"+str(self.parentIndex)
			self.offset = self.offset + self.parent.offset
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

class VSVertex:
	def __init__(self):
		self.group = None;
		self.bone = None;
		self.position = NoeVec3()
		self.idx = -1;
	def hydrate(self, bs, group, bone, i):
		self.idx = i
		self.group = group
		self.bone = bone
		self.position = NoeVec3(bs.read('3h'))
		bs.seek(0x2, NOESEEK_REL)
	def __repr__(self):
		return "(VSVertex :" + str(self.idx) + "," + str(self.bone) + "," + repr(self.position) + ")"

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
		self.type, self.size, self.side, self.alpha = bs.read('4b')
		if self.type == 0x24:
			self.verticesCount = 3
		elif self.type == 0x2C:
			self.verticesCount = 4
		for i in range(0, self.verticesCount):
			idx = int(bs.read('H')[0]/4)
			self.vertices.append(idx)
		for i in range(0, self.verticesCount):
			self.uv.append(bs.read('2B'))
	def __repr__(self):
		return "(VSFace :" + repr(self.vertices) + ")"

def VS_Anim(bs, index, numBones):
	idx = index;
	length = bs.read('H')[0]
	# some animations use a different animation as base
	idOtherAnimation = bs.read('b')[0]
	mode = bs.read('B')[0] # unknown. has weird effects on mesh. 4

	
	ptr1 = bs.read('H')[0] # seems to point to a data block that controls looping
	ptrTranslation = int(bs.read('H')[0]) # points to a translation vector for the animated mesh
	ptrMove = bs.read('H')[0] # points to a data block that controls movement
	ptrBones = [] # read pointers to pose and keyframes for individual bones

	for i in range(0, numBones):
		ptr = bs.read('H')[0]
		ptrBones.append( ptr )
		
	for i in range(0, numBones):
		bs.seek(0x2, NOESEEK_REL)

	return Anim(idx, length, idOtherAnimation, mode, ptr1, ptrTranslation, ptrMove, ptrBones, numBones)
class Anim:
	def __init__(self, idx, length, idOtherAnimation, mode, ptr1, ptrTranslation, ptrMove, ptrBones, numBones):
		self.idx = idx
		self.length = length
		self.idOtherAnimation = idOtherAnimation
		self.mode = mode
		self.ptr1 = ptr1
		self.ptrTranslation = ptrTranslation
		self.ptrMove = ptrMove
		self.ptrBones = ptrBones
		self.numBones = numBones
		self.pose = []
		self.keyframes = [];
	def getData(self, bs, basePtr, dataPtr, animations):
		localPtr = self.ptrTranslation+basePtr+dataPtr
		bs.setOffset(localPtr)
		x = bs.read('h')[0] # BIG_ENDIAN
		y = bs.read('h')[0] # BIG_ENDIAN
		z = bs.read('h')[0] # BIG_ENDIAN
		
		if self.idOtherAnimation != -1:
			self = animations[ self.idOtherAnimation ]
			
		for i in range(0, self.numBones):
			self.keyframes.append( [ [ 0, 0, 0, 0 ] ] )
			localPtr2 = self.ptrBones[i]+basePtr+dataPtr
			bs.setOffset(localPtr2)
			# readPose
			# big endian! but... WHY?!
			rx = bs.read('h')[0] # BIG_ENDIAN
			ry = bs.read('h')[0] # BIG_ENDIAN
			rz = bs.read('h')[0] # BIG_ENDIAN
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
		op0 = op;
		if ( op == 0 ):
			return None
		
		x = 0
		y = 0
		z = 0
		f = 0
		
		if ( op & 0xe0 ) > 0 :
			f = op & 0x1f;
			if f == 0x1f :
				f = 0x20 + bs.read('B')[0]
			else:
				f = 1+f
		else:
			f = op & 0x3;
			if f == 0x3 :
				f = 4 + bs.read('B')[0]
			else:
				f = 1+f
			
			op = op << 3
			h = bs.read('h')[0] # BIG_ENDIAN
			
			if ( h & 0x4 ) > 0 :
				x = h >> 3;
				op = op & 0x60
				
				if ( h & 0x2 ) > 0 :
					y = bs.read('h')[0] # BIG_ENDIAN
					op = op & 0xa0

				if ( h & 0x1 ) > 0 :
					z = bs.read('h')[0] # BIG_ENDIAN
					op = op & 0xc0
			elif ( h & 0x2 ) > 0 :
				y = h >> 3
				op = op & 0xa0
				if ( h & 0x1 ) > 0 :
					z = bs.read('h')[0] # BIG_ENDIAN
					op = op & 0xc0
			elif ( h & 0x1 ) > 0 :
				z = h >> 3
				op = op & 0xc0
				
		# byte values (fallthrough)
		if ( op & 0x80 ) > 0 :
			x = bs.read('b')[0]
		if ( op & 0x40 ) > 0 :
			y = bs.read('b')[0]
		if ( op & 0x20 ) > 0 :
			z = bs.read('b')[0]
		
		return [ x, y, z, f ];
	
	def build(self, model):
		animName = "anim_"+str(self.idx)
		numAnimBones = self.numBones
		animBones = model.bones
		animNumFrames = len(self.keyframes)
		animFrameRate = 24
		numFrameMats = len(self.pose)
		animFrameMats = []
		hierarchy = []

		for i in range(0, len(self.keyframes)):
			frames = self.keyframes[i]
			pose = self.pose[i]
			rx = pose[0]*2
			ry = pose[1]*2
			rz = pose[2]*2

			keys = []
			t = 0

			for j in range(0, len(frames)):
				frame = frames[j]
				f = frame[3]
				t = t+f
				if frame[0] == None:
					frame[0] = frames[j-1][0]
				if frame[1] == None:
					frame[1] = frames[j-1][1]
				if frame[2] == None:
					frame[2] = frames[j-1][2]

				rx = rx + frame[0]*f
				ry = ry + frame[1]*f
				ry = ry + frame[2]*f

				angles = NoeAngles((rx, ry, rz))
				quat = angles.toQuat()
				keys.append(quat.toMat43(int(t))) # timescale
			
			hierarchy = hierarchy + keys
		hierarchy = hierarchy + [NoeMat43()] # root's translation bone

		for i in range(1, self.numBones):
			mat = NoeMat43()
			mat[0][0] = model.bones[i].getMatrix()[0][0]
			hierarchy = hierarchy + [mat]

		return NoeAnim(animName, animBones, animNumFrames, hierarchy, animFrameRate)

def color16to32( c ):
	b = ( c & 0x7C00 ) >> 10
	g = ( c & 0x03E0 ) >> 5
	r = ( c & 0x001F )
	if c == 0 :
		return [ 0, 0, 0, 0 ]
	
	#5bit -> 8bit is factor 2^3 = 8
	return [ r * 8, g * 8, b * 8, 255 ]

def rot13toRad(angle):
	return angle*(1/4096)*math.pi