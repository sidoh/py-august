import unittest
from unittest.mock import patch, Mock

from requests import RequestException

from august.authenticator import Authenticator, AuthenticationState, \
    ValidationResult


class TestAuthenticator(unittest.TestCase):
    def setUp(self):
        """Setup things to be run when tests are started."""

    def _create_authenticator(self, mock_api):
        return Authenticator(mock_api, "phone", "user", "pass",
                             install_id="install_id")

    def _setup_session_response(self, mock_api, v_password, v_install_id):
        session_response = Mock()
        session_response.headers = {
            "x-august-access-token": "access_token"
        }
        session_response.json.return_value = {
            "expiresAt": "",
            "vPassword": v_password,
            "vInstallId": v_install_id
        }
        mock_api.get_session.return_value = session_response

    @patch('august.api.Api')
    def test_get_session_with_authenticated_response(self, mock_api):
        self._setup_session_response(mock_api, True, True)

        authenticator = self._create_authenticator(mock_api)
        authentication = authenticator.authenticate()

        mock_api.get_session.assert_called_once_with("install_id",
                                                     "phone:user", "pass")

        self.assertEqual("access_token", authentication.access_token)
        self.assertEqual("install_id", authentication.install_id)
        self.assertEqual(AuthenticationState.AUTHENTICATED,
                         authentication.state)

    @patch('august.api.Api')
    def test_get_session_with_bad_password_response(self, mock_api):
        self._setup_session_response(mock_api, False, True)

        authenticator = self._create_authenticator(mock_api)
        authentication = authenticator.authenticate()

        mock_api.get_session.assert_called_once_with("install_id",
                                                     "phone:user", "pass")

        self.assertEqual("access_token", authentication.access_token)
        self.assertEqual("install_id", authentication.install_id)
        self.assertEqual(AuthenticationState.BAD_PASSWORD,
                         authentication.state)

    @patch('august.api.Api')
    def test_get_session_with_requires_validation_response(self, mock_api):
        self._setup_session_response(mock_api, True, False)

        authenticator = self._create_authenticator(mock_api)
        authentication = authenticator.authenticate()

        mock_api.get_session.assert_called_once_with("install_id",
                                                     "phone:user", "pass")

        self.assertEqual("access_token", authentication.access_token)
        self.assertEqual("install_id", authentication.install_id)
        self.assertEqual(AuthenticationState.REQUIRES_VALIDATION,
                         authentication.state)

    @patch('august.api.Api')
    def test_get_session_with_already_authenticated_state(self, mock_api):
        self._setup_session_response(mock_api, True, True)

        authenticator = self._create_authenticator(mock_api)
        # this will set authentication state to AUTHENTICATED
        authenticator.authenticate()
        # call authenticate() again
        authentication = authenticator.authenticate()

        mock_api.get_session.assert_called_once_with("install_id",
                                                     "phone:user", "pass")

        self.assertEqual("access_token", authentication.access_token)
        self.assertEqual("install_id", authentication.install_id)
        self.assertEqual(AuthenticationState.AUTHENTICATED,
                         authentication.state)

    @patch('august.api.Api')
    def test_send_verification_code(self, mock_api):
        self._setup_session_response(mock_api, True, False)

        authenticator = self._create_authenticator(mock_api)
        authenticator.authenticate()
        authenticator.send_verification_code()

        mock_api.send_verification_code.assert_called_once_with(
            "access_token",
            "phone",
            "user")

    @patch('august.api.Api')
    def test_validate_verification_code_with_no_code(self, mock_api):
        self._setup_session_response(mock_api, True, False)

        authenticator = self._create_authenticator(mock_api)
        authenticator.authenticate()
        result = authenticator.validate_verification_code("")

        mock_api.validate_verification_code.assert_not_called()

        self.assertEqual(ValidationResult.INVALID_VERIFICATION_CODE, result)

    @patch('august.api.Api')
    def test_validate_verification_code_with_validated_response(self,
                                                                mock_api):
        self._setup_session_response(mock_api, True, False)

        response = Mock()
        mock_api.validate_verification_code.return_value = response

        authenticator = self._create_authenticator(mock_api)
        authenticator.authenticate()
        result = authenticator.validate_verification_code("123456")

        mock_api.validate_verification_code.assert_called_once_with(
            "access_token",
            "phone",
            "user",
            "123456")

        self.assertEqual(ValidationResult.VALIDATED, result)

    @patch('august.api.Api')
    def test_validate_verification_code_with_invalid_code_response(self,
                                                                   mock_api):
        self._setup_session_response(mock_api, True, False)

        mock_api.validate_verification_code.side_effect = RequestException()

        authenticator = self._create_authenticator(mock_api)
        authenticator.authenticate()
        result = authenticator.validate_verification_code("123456")

        mock_api.validate_verification_code.assert_called_once_with(
            "access_token",
            "phone",
            "user",
            "123456")

        self.assertEqual(ValidationResult.INVALID_VERIFICATION_CODE, result)
