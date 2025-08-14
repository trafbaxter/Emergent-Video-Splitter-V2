import React, { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';

const AdminDashboard = () => {
  const { user, accessToken, API_BASE } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Filter states
  const [statusFilter, setStatusFilter] = useState('all');
  const [roleFilter, setRoleFilter] = useState('all');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/admin/users`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUsers(data.users || []);
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Failed to fetch users');
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleUserAction = async (userId, action, notes = '') => {
    try {
      setActionLoading(true);
      const response = await fetch(`${API_BASE}/api/admin/users/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId, action, notes })
      });

      if (response.ok) {
        const data = await response.json();
        alert(`User ${action}d successfully!`);
        fetchUsers(); // Refresh user list
        setSelectedUser(null);
      } else {
        const errorData = await response.json();
        alert(`Failed to ${action} user: ${errorData.message}`);
      }
    } catch (error) {
      console.error(`Error ${action}ing user:`, error);
      alert(`Network error while ${action}ing user`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
      return;
    }

    try {
      setActionLoading(true);
      const response = await fetch(`${API_BASE}/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        alert('User deleted successfully!');
        fetchUsers(); // Refresh user list
      } else {
        const errorData = await response.json();
        alert(`Failed to delete user: ${errorData.message}`);
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      alert('Network error while deleting user');
    } finally {
      setActionLoading(false);
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesStatus = statusFilter === 'all' || user.approval_status === statusFilter;
    const matchesRole = roleFilter === 'all' || user.user_role === roleFilter;
    return matchesStatus && matchesRole && !user.deleted;
  });

  const getStatusBadge = (status) => {
    const colors = {
      'pending': 'background: #fff3cd; color: #856404; border: 1px solid #ffeaa7',
      'approved': 'background: #d4edda; color: #155724; border: 1px solid #c3e6cb',
      'rejected': 'background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb'
    };

    return (
      <span style={{
        ...colors[status] ? { cssText: colors[status] } : { background: '#e2e3e5', color: '#495057' },
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '12px',
        fontWeight: 'bold',
        textTransform: 'uppercase'
      }}>
        {status}
      </span>
    );
  };

  const getRoleBadge = (role) => {
    const isAdmin = role === 'admin';
    return (
      <span style={{
        background: isAdmin ? '#dc3545' : '#6c757d',
        color: 'white',
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '12px',
        fontWeight: 'bold',
        textTransform: 'uppercase'
      }}>
        {role}
      </span>
    );
  };

  if (!user || user.role !== 'admin') {
    return (
      <div style={{ 
        padding: '40px 20px', 
        textAlign: 'center',
        color: '#721c24',
        backgroundColor: '#f8d7da',
        border: '1px solid #f5c6cb',
        borderRadius: '8px',
        margin: '20px'
      }}>
        <h2>Access Denied</h2>
        <p>You need administrator privileges to access this page.</p>
      </div>
    );
  }

  return (
    <div style={{ 
      padding: '20px',
      maxWidth: '1200px',
      margin: '0 auto'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '30px',
        padding: '20px',
        backgroundColor: '#fff',
        borderRadius: '8px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <div>
          <h1 style={{ margin: 0, color: '#333' }}>Admin Dashboard</h1>
          <p style={{ margin: '5px 0 0 0', color: '#666' }}>
            Manage users and system access
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          style={{
            padding: '10px 20px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: 'bold'
          }}
        >
          + Create New User
        </button>
      </div>

      {/* Stats Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '20px',
        marginBottom: '30px'
      }}>
        <div style={{
          padding: '20px',
          backgroundColor: '#fff',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>Total Users</h3>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#007bff' }}>
            {users.filter(u => !u.deleted).length}
          </div>
        </div>
        <div style={{
          padding: '20px',
          backgroundColor: '#fff',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>Pending Approval</h3>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ffc107' }}>
            {users.filter(u => u.approval_status === 'pending' && !u.deleted).length}
          </div>
        </div>
        <div style={{
          padding: '20px',
          backgroundColor: '#fff',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>Active Users</h3>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#28a745' }}>
            {users.filter(u => u.approval_status === 'approved' && !u.deleted).length}
          </div>
        </div>
        <div style={{
          padding: '20px',
          backgroundColor: '#fff',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>Admins</h3>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#dc3545' }}>
            {users.filter(u => u.user_role === 'admin' && !u.deleted).length}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div style={{
        padding: '20px',
        backgroundColor: '#fff',
        borderRadius: '8px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        marginBottom: '20px',
        display: 'flex',
        gap: '20px',
        alignItems: 'center'
      }}>
        <div>
          <label style={{ marginRight: '10px', fontWeight: 'bold' }}>Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              padding: '5px 10px',
              border: '1px solid #ccc',
              borderRadius: '4px'
            }}
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
        <div>
          <label style={{ marginRight: '10px', fontWeight: 'bold' }}>Role:</label>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            style={{
              padding: '5px 10px',
              border: '1px solid #ccc',
              borderRadius: '4px'
            }}
          >
            <option value="all">All Roles</option>
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <button
          onClick={fetchUsers}
          style={{
            padding: '8px 16px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Refresh
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div style={{
          padding: '15px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          borderRadius: '8px',
          marginBottom: '20px',
          border: '1px solid #f5c6cb'
        }}>
          {error}
        </div>
      )}

      {/* Users Table */}
      <div style={{
        backgroundColor: '#fff',
        borderRadius: '8px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        overflow: 'hidden'
      }}>
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center' }}>
            <div>Loading users...</div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8f9fa' }}>
                  <th style={{ padding: '15px', textAlign: 'left', borderBottom: '1px solid #dee2e6' }}>
                    User
                  </th>
                  <th style={{ padding: '15px', textAlign: 'left', borderBottom: '1px solid #dee2e6' }}>
                    Role
                  </th>
                  <th style={{ padding: '15px', textAlign: 'left', borderBottom: '1px solid #dee2e6' }}>
                    Status
                  </th>
                  <th style={{ padding: '15px', textAlign: 'left', borderBottom: '1px solid #dee2e6' }}>
                    Created
                  </th>
                  <th style={{ padding: '15px', textAlign: 'left', borderBottom: '1px solid #dee2e6' }}>
                    Last Login
                  </th>
                  <th style={{ padding: '15px', textAlign: 'center', borderBottom: '1px solid #dee2e6' }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((user) => (
                  <tr key={user.user_id} style={{ borderBottom: '1px solid #dee2e6' }}>
                    <td style={{ padding: '15px' }}>
                      <div>
                        <div style={{ fontWeight: 'bold' }}>
                          {user.first_name} {user.last_name}
                        </div>
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          {user.email}
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: '15px' }}>
                      {getRoleBadge(user.user_role)}
                    </td>
                    <td style={{ padding: '15px' }}>
                      {getStatusBadge(user.approval_status)}
                    </td>
                    <td style={{ padding: '15px', fontSize: '12px', color: '#666' }}>
                      {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td style={{ padding: '15px', fontSize: '12px', color: '#666' }}>
                      {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                    </td>
                    <td style={{ padding: '15px', textAlign: 'center' }}>
                      <div style={{ display: 'flex', gap: '5px', justifyContent: 'center' }}>
                        {user.approval_status === 'pending' && (
                          <>
                            <button
                              onClick={() => handleUserAction(user.user_id, 'approve')}
                              disabled={actionLoading}
                              style={{
                                padding: '5px 10px',
                                backgroundColor: '#28a745',
                                color: 'white',
                                border: 'none',
                                borderRadius: '3px',
                                cursor: 'pointer',
                                fontSize: '12px'
                              }}
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleUserAction(user.user_id, 'reject')}
                              disabled={actionLoading}
                              style={{
                                padding: '5px 10px',
                                backgroundColor: '#dc3545',
                                color: 'white',
                                border: 'none',
                                borderRadius: '3px',
                                cursor: 'pointer',
                                fontSize: '12px'
                              }}
                            >
                              Reject
                            </button>
                          </>
                        )}
                        {user.user_role !== 'admin' && (
                          <button
                            onClick={() => handleDeleteUser(user.user_id)}
                            disabled={actionLoading}
                            style={{
                              padding: '5px 10px',
                              backgroundColor: '#6c757d',
                              color: 'white',
                              border: 'none',
                              borderRadius: '3px',
                              cursor: 'pointer',
                              fontSize: '12px'
                            }}
                          >
                            Delete
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {filteredUsers.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
                      No users found matching the current filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create User Modal */}
      {showCreateForm && (
        <CreateUserModal
          onClose={() => setShowCreateForm(false)}
          onUserCreated={fetchUsers}
          accessToken={accessToken}
          API_BASE={API_BASE}
        />
      )}
    </div>
  );
};

// Create User Modal Component
const CreateUserModal = ({ onClose, onUserCreated, accessToken, API_BASE }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    firstName: '',
    lastName: '',
    role: 'user',
    forcePasswordChange: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/admin/users`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const data = await response.json();
        alert('User created successfully!');
        onUserCreated(); // Refresh the user list
        onClose(); // Close the modal
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Failed to create user');
      }
    } catch (error) {
      console.error('Error creating user:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '30px',
        borderRadius: '8px',
        width: '90%',
        maxWidth: '500px',
        maxHeight: '90vh',
        overflowY: 'auto'
      }}>
        <h2 style={{ marginTop: 0 }}>Create New User</h2>
        
        {error && (
          <div style={{
            padding: '10px',
            backgroundColor: '#f8d7da',
            color: '#721c24',
            borderRadius: '4px',
            marginBottom: '15px',
            border: '1px solid #f5c6cb'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Email *
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              required
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '14px',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Password *
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              required
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '14px',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              First Name *
            </label>
            <input
              type="text"
              name="firstName"
              value={formData.firstName}
              onChange={handleInputChange}
              required
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '14px',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Last Name *
            </label>
            <input
              type="text"
              name="lastName"
              value={formData.lastName}
              onChange={handleInputChange}
              required
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '14px',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Role *
            </label>
            <select
              name="role"
              value={formData.role}
              onChange={handleInputChange}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '14px',
                boxSizing: 'border-box'
              }}
            >
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <input
                type="checkbox"
                name="forcePasswordChange"
                checked={formData.forcePasswordChange}
                onChange={(e) => setFormData({...formData, forcePasswordChange: e.target.checked})}
              />
              <span>Force password change on first login</span>
            </label>
          </div>

          <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '10px 20px',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              style={{
                padding: '10px 20px',
                backgroundColor: loading ? '#6c757d' : '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? 'Creating...' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AdminDashboard;