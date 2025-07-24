import { BillingPlan } from '../types/api';

interface FeatureAccess {
  canUseAIChat: boolean;
  canAutoFixErrors: boolean;
  canUseAdvancedTemplates: boolean;
  canUseCustomContainers: boolean;
  canExportCode: boolean;
  hasVersionControl: boolean;
  hasCollaboration: boolean;
  hasAnalytics: boolean;
  hasPrioritySupport: boolean;
  canUseCustomModels: boolean;
  hasAPIAccess: boolean;
  hasWhiteLabeling: boolean;
}

export function useFeatureAccess(userPlan?: BillingPlan): FeatureAccess {
  if (!userPlan) {
    // Return default free plan permissions when no plan is provided
    return {
      canUseAIChat: true,
      canAutoFixErrors: false,
      canUseAdvancedTemplates: false,
      canUseCustomContainers: false,
      canExportCode: true,
      hasVersionControl: false,
      hasCollaboration: false,
      hasAnalytics: false,
      hasPrioritySupport: false,
      canUseCustomModels: false,
      hasAPIAccess: false,
      hasWhiteLabeling: false,
    };
  }

  return {
    canUseAIChat: userPlan.enable_ai_chat ?? false,
    canAutoFixErrors: userPlan.enable_auto_error_fix ?? false,
    canUseAdvancedTemplates: userPlan.enable_advanced_templates ?? false,
    canUseCustomContainers: userPlan.enable_custom_containers ?? false,
    canExportCode: userPlan.enable_code_export ?? true, // Default true
    hasVersionControl: userPlan.enable_version_control ?? false,
    hasCollaboration: userPlan.enable_collaboration ?? false,
    hasAnalytics: userPlan.enable_analytics ?? false,
    hasPrioritySupport: userPlan.enable_priority_support ?? false,
    canUseCustomModels: userPlan.enable_custom_models ?? false,
    hasAPIAccess: userPlan.enable_api_access ?? false,
    hasWhiteLabeling: userPlan.enable_white_labeling ?? false,
  };
}

// Helper function to check individual feature access
export function checkFeatureAccess(feature: keyof BillingPlan, userPlan?: BillingPlan): boolean {
  if (!userPlan) return false;
  return userPlan[feature] as boolean;
}