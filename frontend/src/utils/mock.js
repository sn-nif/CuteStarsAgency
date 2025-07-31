// Mock data for frontend-only functionality
// This will be replaced with actual backend integration later

export const mockApplications = [
  {
    id: 1,
    name: "Sarah Johnson",
    age: 24,
    email: "sarah.j@email.com",
    contact: "+1 (555) 123-4567",
    instagram: "@sarahj_model",
    tiktok: "@sarahj24",
    twitter: "@sarah_johnson",
    photos: [],
    submittedAt: "2025-01-11T10:30:00Z",
    status: "pending"
  },
  {
    id: 2,
    name: "Emma Rodriguez",
    age: 22,
    email: "emma.r@email.com",
    contact: "+1 (555) 987-6543",
    instagram: "@emma_rodriguez",
    tiktok: "@emmarodz",
    twitter: "",
    photos: [],
    submittedAt: "2025-01-10T15:45:00Z",
    status: "approved"
  }
];

// Mock API functions (these simulate backend calls)
export const mockAPI = {
  submitApplication: async (applicationData) => {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const newApplication = {
      id: Date.now(),
      ...applicationData,
      submittedAt: new Date().toISOString(),
      status: "pending"
    };
    
    mockApplications.push(newApplication);
    return newApplication;
  },

  getApplications: async () => {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    return mockApplications;
  },

  getApplicationById: async (id) => {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 500));
    return mockApplications.find(app => app.id === parseInt(id));
  }
};