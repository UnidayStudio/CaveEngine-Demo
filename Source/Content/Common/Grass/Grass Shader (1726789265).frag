// Shader "Default/Renderer/Fragment.glsl"
#include "Default/Header.glsl"

// Inputs from the Vertex Shaders:
in VS_OUT{
	vec3 normal;
	vec3 tangent;
	vec2 texCoord;
	vec3 position;
} fsIn;
in vec4       entityTint;
flat in ivec4 entityID;

// Fragment Shader Outputs:
layout(location = 0) out vec4 gColor;
layout(location = 1) out vec4 gNormal;
layout(location = 2) out vec4 gAssetID;

// Uniforms:
#include "Default/Uniforms/Scene.glsl"    // inScene, _shadowTex, _ambientColor_[...], _mistColor_[...]
#include "Default/Uniforms/Lights.glsl"   // inLights
#include "Default/Uniforms/Material.glsl" // inMaterial, inAlbedo, inRoughness, inMetallic, inNormalMap, inEmission

#include "Default/ColorSampler.glsl"

#include "Math/Random.glsl"
#include "Math/Pbr.glsl"

#ifndef SHADER_SHADOW_PASS // Regular pass bellow:

void mainBasic() { // You can use this one to test things out... :)
	gAssetID = entityID;
	gNormal = vec4(GetMaterialNormal(), GetDistanceToCamera());
	gColor = texture(inAlbedo, GetMaterialUV());
}

void main() {
	gAssetID = entityID;
	gNormal = vec4(GetMaterialNormal(), GetDistanceToCamera());

	vec2 uv = GetMaterialUV();
	vec4 albedo = texture(inAlbedo, uv);
	albedo.rgb *= entityTint.rgb;

	// LOD Dithering if the tint alpha is negative:
	if (entityTint.a < 0) {
		if (abs(entityTint.a) < Random(fsIn.position)) {
			discard;
		}
	}
	else {
		albedo.a *= entityTint.a;
	}
	albedo.a *= inMaterial.alphaValue;

	#ifndef SHADER_ALPHA_BLEND
		float alphaThreshold = inMaterial.alphaValue - 0.01f; // - Bias
		if (albedo.a < alphaThreshold || albedo.a <= 0.f) {
			discard;
		}
	#endif

	gColor = albedo;
	#ifndef SHADER_MATERIAL_SHADELESS
		float shadow = 1.0;
		#ifdef SHADER_SCENE_HAS_SHADOWS
			// Normal here is only used for extra Bias,so we use the model one!
			shadow = GetSceneShadow(fsIn.normal, fsIn.position);
		#endif

		#ifdef SHADER_SCENE_HAS_AMBIENT
			gColor.xyz = GetSceneAmbientFor(albedo.xyz, gNormal.xyz, fsIn.position);
		#endif 

		#ifdef SHADER_SCENE_SHADED
			float metallic = texture(inMetallic, uv).x;
			float roughness = texture(inRoughness, uv).x;

			gColor.xyz += GetPbrColor(gNormal.xyz, shadow, albedo.xyz, metallic, roughness);
		#endif
	#endif

	gColor.xyz += texture(inEmission, uv).rgb * inEmissionScale;

	#ifdef SHADER_SCENE_HAS_MIST
		gColor.xyz = GetSceneMistFor(gColor.xyz, gNormal.xyz, fsIn.position);
	#endif

	// Aperture
	gColor.xyz /= inScene.cameraAperture;
}

#else // SHADER_SHADOW_PASS || Shadow pass bellow:

void main() {
	// LOD Dithering if the tint alpha is negative:
	if (entityTint.a < 0) {
		if (abs(entityTint.a) < fract(length(fsIn.position))) {
			discard;
		}
	}

	// The shadow pass only updates the albedo texture is alphaValue is < 1.0!
	if (inMaterial.alphaValue < 0.99999f) {
		vec2 uv = GetMaterialUV();
		vec4 albedo = texture(inAlbedo, uv);

		if (entityTint.a >= 0) {
			albedo.a *= entityTint.a;
		}
		albedo.a *= inMaterial.alphaValue;

		float alphaThreshold = inMaterial.alphaValue - 0.01f; // - Bias
		if (albedo.a < alphaThreshold) {
			discard; // Discard alpha
		}
	}
}


#endif // SHADER_SHADOW_PASS
