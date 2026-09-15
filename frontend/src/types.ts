export interface Company { id: string; tenant_id: string; name: string; is_active: boolean }
export interface Worker extends Company { company_id: string; registration: string }
export interface Identity { user: { id: string; email: string; is_active: boolean }; tenant_id: string }
export interface Tenant { id: string; name: string }
