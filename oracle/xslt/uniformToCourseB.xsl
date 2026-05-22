<?xml version="1.0" encoding="UTF-8"?>
<!-- 统一集成格式 → B(Oracle) 课程格式 -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <Classes>
      <xsl:for-each select="Classes/class">
        <class>
          <id><xsl:value-of select="id"/></id>
          <name><xsl:value-of select="name"/></name>
          <time><xsl:value-of select="hours"/></time>
          <score><xsl:value-of select="credit"/></score>
          <teacher><xsl:value-of select="teacher"/></teacher>
          <location><xsl:value-of select="location"/></location>
          <shareFlag><xsl:value-of select="share_flag"/></shareFlag>
          <capacity>60</capacity>
          <status>OPEN</status>
        </class>
      </xsl:for-each>
    </Classes>
  </xsl:template>

</xsl:stylesheet>
