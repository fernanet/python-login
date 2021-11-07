CREATE DATABASE IF NOT EXISTS `ciscorp_bd` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `ciscorp_bd`;

CREATE TABLE IF NOT EXISTS `contas` (
`id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario` varchar(50) NOT NULL,
  `senha` varchar(255) NOT NULL,
  `email` varchar(100) NOT NULL,
  `funcao` enum('Usuário','Admin') NOT NULL DEFAULT 'Usuário',
  `cod_ativ` varchar(255) NOT NULL DEFAULT '',
  `lembranca` varchar(255) NOT NULL DEFAULT '',
  `reset` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;

INSERT INTO `contas` (`id`, `usuario`, `senha`, `email`, `funcao`, `cod_ativ`, `lembranca`, `reset`) VALUES
(1, 'admin', 'b9fc65789ca65526a77b0009f24e9c01a43e32b3', 'admin@ciscorp.com.br', 'Admin', 'ativado', '', ''),
(2, 'usuario', 'f046926a90af0b97acbc451bcbde266878f5f963', 'usuario@ciscorp.com.br', 'Usuário', 'ativado', '', '');